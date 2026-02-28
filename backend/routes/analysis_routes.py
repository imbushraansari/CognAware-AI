import json
import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from backend.models.thought import Thought
from backend.services.model_service import DISTORTION_LABELS, analyze_thought
from backend.services.explanation_service import assess_safety_risk
from backend.services.reframing_service import build_reframe_suggestion
from backend.database.db_init import db

analysis_bp = Blueprint("analysis", __name__)
logger = logging.getLogger(__name__)


def _build_dashboard_prediction(results_payload):
	probability_source = {}
	top_distortions_source = []
	confidence_label = None
	if isinstance(results_payload, dict):
		if isinstance(results_payload.get("probabilities"), dict):
			probability_source = results_payload.get("probabilities", {})
		else:
			probability_source = results_payload

		top_distortions_source = results_payload.get("top_distortions", [])
		confidence_label = results_payload.get("confidence_label")

	probabilities = {}
	for label in DISTORTION_LABELS:
		value = probability_source.get(label, 0.0)
		try:
			probabilities[label] = float(value)
		except (TypeError, ValueError):
			probabilities[label] = 0.0

	sorted_distortions = sorted(
		probabilities.items(),
		key=lambda item: item[1],
		reverse=True,
	)
	top_distortions = []
	if isinstance(top_distortions_source, list):
		for item in top_distortions_source:
			if not isinstance(item, (list, tuple)) or len(item) != 2:
				continue
			label, value = item
			if label not in probabilities:
				continue
			try:
				top_distortions.append((label, float(value)))
			except (TypeError, ValueError):
				top_distortions.append((label, 0.0))

	if not top_distortions:
		top_distortions = sorted_distortions[:3]
	elif len(top_distortions) < 3:
		present_labels = {label for label, _ in top_distortions}
		for label, value in sorted_distortions:
			if label in present_labels:
				continue
			top_distortions.append((label, value))
			if len(top_distortions) == 3:
				break
	else:
		top_distortions = top_distortions[:3]

	max_probability = sorted_distortions[0][1] if sorted_distortions else 0.0
	high_confidence = max_probability >= 0.25

	if not confidence_label:
		if max_probability >= 0.25:
			confidence_label = "Strong Signal"
		elif max_probability >= 0.10:
			confidence_label = "Moderate Signal"
		else:
			confidence_label = "Mild Signal"

	return {
		"probabilities": probabilities,
		"sorted_distortions": sorted_distortions,
		"top_distortions": top_distortions,
		"max_probability": max_probability,
		"high_confidence": high_confidence,
		"confidence_label": confidence_label,
	}


def _build_pattern_insight(thought_predictions):
	if len(thought_predictions) < 4:
		return {"status": "insufficient_data"}

	midpoint = len(thought_predictions) // 2
	earlier_half = thought_predictions[:midpoint]
	recent_half = thought_predictions[midpoint:]

	label_averages = {}
	for label in DISTORTION_LABELS:
		total = sum(float(item["probabilities"].get(label, 0.0)) for item in thought_predictions)
		label_averages[label] = total / len(thought_predictions)

	most_frequent_distortion = max(label_averages.items(), key=lambda item: item[1])[0]

	def _mean_intensity(entries):
		if not entries:
			return 0.0
		intensities = []
		for entry in entries:
			probabilities = entry.get("probabilities", {})
			mean_value = sum(float(probabilities.get(label, 0.0)) for label in DISTORTION_LABELS) / len(DISTORTION_LABELS)
			intensities.append(mean_value)
		return sum(intensities) / len(intensities)

	earlier_intensity = _mean_intensity(earlier_half)
	recent_intensity = _mean_intensity(recent_half)

	if earlier_intensity == 0:
		change = 0.0 if recent_intensity == 0 else 100.0
	else:
		change = ((recent_intensity - earlier_intensity) / earlier_intensity) * 100

	if change < 0:
		trend = "decreasing"
	elif change > 0:
		trend = "increasing"
	else:
		trend = "stable"

	return {
		"most_frequent": most_frequent_distortion,
		"change_percent": round(change, 2),
		"trend": trend,
	}


@analysis_bp.route("/dashboard", methods=["GET", "POST"], strict_slashes=False)
@login_required
def dashboard():
	if request.method == "POST":
		thought_text = request.form.get("thought", "").strip()

		if not thought_text:
			flash("Please enter a thought before analyzing.", "warning")
			return redirect(url_for("analysis.dashboard"))

		try:
			prediction = analyze_thought(thought_text)
		except Exception:
			logger.exception("Dashboard analysis failed for user_id=%s", current_user.id)
			flash("Analysis failed. Please try again.", "danger")
			return redirect(url_for("analysis.dashboard"))

		thought = Thought(
			user_id=current_user.id,
			text=thought_text,
			results=json.dumps(prediction),
		)
		db.session.add(thought)
		db.session.commit()

		flash("Thought analyzed and saved successfully.", "success")
		return redirect(url_for("analysis.dashboard"))

	thoughts = (
		Thought.query.filter_by(user_id=current_user.id)
		.order_by(Thought.created_at.desc())
		.all()
	)

	thought_history = []
	for thought in thoughts:
		try:
			parsed_results = json.loads(thought.results)
		except (TypeError, json.JSONDecodeError):
			logger.warning("Invalid JSON in thought results. thought_id=%s", thought.id)
			parsed_results = {}

		dashboard_prediction = _build_dashboard_prediction(parsed_results)

		thought_history.append(
			{
				"id": thought.id,
				"text": thought.text,
				"results": dashboard_prediction["probabilities"],
				"sorted_distortions": dashboard_prediction["sorted_distortions"],
				"top_distortions": dashboard_prediction["top_distortions"],
				"max_probability": dashboard_prediction["max_probability"],
				"high_confidence": dashboard_prediction["high_confidence"],
				"confidence_label": dashboard_prediction["confidence_label"],
				"created_at": thought.created_at,
			}
		)

	return render_template("dashboard.html", thoughts=thought_history, prediction=None)


@analysis_bp.route("/analysis/result/<int:thought_id>")
@login_required
def analysis_result(thought_id):
	user_thoughts = (
		Thought.query.filter_by(user_id=current_user.id)
		.order_by(Thought.created_at.asc())
		.all()
	)

	selected_thought = next((item for item in user_thoughts if item.id == thought_id), None)
	if selected_thought is None:
		flash("Thought not found.", "warning")
		return redirect(url_for("analysis.dashboard"))

	thought_predictions = []
	distortion_history = []
	top_distortion_frequency = {}
	for thought in user_thoughts:
		try:
			parsed_results = json.loads(thought.results)
		except (TypeError, json.JSONDecodeError):
			logger.warning("Invalid JSON in thought results. thought_id=%s", thought.id)
			parsed_results = {}

		dashboard_prediction = _build_dashboard_prediction(parsed_results)
		distortion_history.append(float(dashboard_prediction["max_probability"]))

		top_distortions = dashboard_prediction.get("top_distortions", [])
		if top_distortions:
			top_label = top_distortions[0][0]
			top_distortion_frequency[top_label] = top_distortion_frequency.get(top_label, 0) + 1

		thought_predictions.append(
			{
				"thought_id": thought.id,
				"probabilities": dashboard_prediction["probabilities"],
				"top_distortions": top_distortions,
				"max_probability": dashboard_prediction["max_probability"],
				"confidence_label": dashboard_prediction["confidence_label"],
			}
		)

	current_prediction = next(
		(item for item in thought_predictions if item["thought_id"] == selected_thought.id),
		None,
	)
	if current_prediction is None:
		flash("Analysis result not available.", "warning")
		return redirect(url_for("analysis.dashboard"))

	current_score = float(current_prediction.get("max_probability", 0.0))
	history_length = len(distortion_history)

	if history_length >= 2:
		previous_scores = distortion_history[:-1]
		previous_avg = sum(previous_scores) / len(previous_scores) if previous_scores else 0.0
	else:
		previous_avg = current_score

	overall_avg = sum(distortion_history) / history_length if history_length else 0.0

	if current_score < previous_avg - 0.05:
		trend = "Improving"
	elif current_score > previous_avg + 0.05:
		trend = "Increasing Distortion"
	else:
		trend = "Stable"

	if top_distortion_frequency:
		most_frequent_distortion = max(top_distortion_frequency.items(), key=lambda item: item[1])[0]
	else:
		most_frequent_distortion = "N/A"

	pattern_insight = _build_pattern_insight(thought_predictions)
	safety_assessment = assess_safety_risk(selected_thought.text)
	reframe_suggestion = build_reframe_suggestion(
		current_prediction.get("top_distortions", []),
		selected_thought.text,
	)

	return render_template(
		"analysis_result.html",
		prediction=current_prediction,
		pattern_insight=pattern_insight,
		safety_assessment=safety_assessment,
		reframe_suggestion=reframe_suggestion,
		thought_text=selected_thought.text,
		trend=trend,
		current_score=current_score,
		previous_avg=previous_avg,
		overall_avg=overall_avg,
		most_frequent_distortion=most_frequent_distortion,
		history_length=history_length,
	)
