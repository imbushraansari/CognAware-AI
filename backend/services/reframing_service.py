DISTORTION_REFRAME_GUIDE = {
	"overgeneralization": {
		"challenge": "Is this one event, or a permanent pattern across all situations?",
		"reframe": "One difficult moment does not define your full ability. I can learn from this specific event and improve.",
	},
	"catastrophizing": {
		"challenge": "What is the most realistic outcome, not just the worst-case outcome?",
		"reframe": "This feels intense right now, but I can handle it step by step and most outcomes are manageable.",
	},
	"mind_reading": {
		"challenge": "What actual evidence do I have about what others think?",
		"reframe": "I cannot know others' thoughts without communication. I can ask clearly instead of assuming.",
	},
	"emotional_reasoning": {
		"challenge": "Am I treating a feeling as a fact?",
		"reframe": "My feelings are valid signals, but they are not always facts. I can pause and verify the situation.",
	},
	"black_white_thinking": {
		"challenge": "Is there a middle ground between perfect and failure?",
		"reframe": "Progress exists between extremes. I can be imperfect and still moving forward.",
	},
	"personalization": {
		"challenge": "Am I taking responsibility for factors outside my control?",
		"reframe": "I can own my part without blaming myself for everything. Many factors influence outcomes.",
	},
}


def build_reframe_suggestion(top_distortions: list, thought_text: str = "") -> dict:
	if not top_distortions:
		return {
			"primary_distortion": "none",
			"challenge_question": "What is one balanced way to view this situation?",
			"balanced_reframe": "I can pause, gather facts, and respond with self-compassion.",
		}

	primary_label = str(top_distortions[0][0]).strip().lower()
	guide = DISTORTION_REFRAME_GUIDE.get(primary_label)

	if not guide:
		return {
			"primary_distortion": primary_label,
			"challenge_question": "What evidence supports and challenges this thought?",
			"balanced_reframe": "I can hold a more balanced perspective and act on what is within my control.",
		}

	return {
		"primary_distortion": primary_label,
		"challenge_question": guide["challenge"],
		"balanced_reframe": guide["reframe"],
	}
