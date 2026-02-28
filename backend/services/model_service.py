import os
import logging

import joblib
import numpy as np


DISTORTION_LABELS = [
    "overgeneralization",
    "catastrophizing",
    "mind_reading",
    "emotional_reasoning",
    "black_white_thinking",
    "personalization",
]


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
CLASSIFIER_PATH = os.path.join(MODELS_DIR, "distortion_classifier.joblib")
EMBEDDER_PATH = os.path.join(MODELS_DIR, "embedding_model.joblib")


logger = logging.getLogger(__name__)


try:
    classifier_model = joblib.load(CLASSIFIER_PATH)
    embedding_model = joblib.load(EMBEDDER_PATH)
except Exception as error:
    logger.exception("Failed to load model artifacts from disk.")
    classifier_model = None
    embedding_model = None


def _normalize_label(label):
    return str(label).strip().lower().replace(" ", "_").replace("-", "_")


def _generate_embedding(text):
    if hasattr(embedding_model, "encode"):
        embedding = embedding_model.encode([text])
    elif hasattr(embedding_model, "transform"):
        embedding = embedding_model.transform([text])
    else:
        raise AttributeError("Loaded embedding model does not support encode or transform.")

    if hasattr(embedding, "toarray"):
        embedding = embedding.toarray()

    return embedding


def analyze_thought(text):
    if classifier_model is None or embedding_model is None:
        message = "Models not loaded properly. Ensure classifier and embedding artifacts are available."
        logger.error(message)
        raise RuntimeError(message)

    embedding = _generate_embedding(text)
    embedding = np.asarray(embedding)
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)
    elif embedding.ndim > 2:
        embedding = embedding.reshape(embedding.shape[0], -1)

    expected_features = getattr(classifier_model, "n_features_in_", None)
    if expected_features is not None and embedding.shape[1] != int(expected_features):
        message = (
            f"Embedding dimension mismatch: got {embedding.shape[1]}, "
            f"expected {int(expected_features)}"
        )
        logger.error(message)
        raise ValueError(message)

    try:
        raw_probabilities = classifier_model.predict_proba(embedding)
    except Exception as error:
        logger.exception("Prediction failed during predict_proba.")
        raise RuntimeError(f"Failed to compute prediction probabilities: {error}") from error

    probabilities = []

    if isinstance(raw_probabilities, list):
        for class_output in raw_probabilities:
            class_output = np.asarray(class_output)
            if class_output.ndim >= 2 and class_output.shape[0] > 0 and class_output.shape[1] >= 2:
                probabilities.append(float(class_output[0][1]))
            elif class_output.ndim == 1 and class_output.size >= 2:
                probabilities.append(float(class_output[1]))
            elif class_output.size > 0:
                probabilities.append(float(class_output.reshape(-1)[0]))
            else:
                probabilities.append(0.0)
    else:
        probability_array = np.asarray(raw_probabilities)

        if probability_array.ndim == 3 and probability_array.shape[-1] >= 2:
            if probability_array.shape[0] == 1:
                for class_index in range(probability_array.shape[1]):
                    probabilities.append(float(probability_array[0][class_index][1]))
            else:
                for class_index in range(probability_array.shape[0]):
                    probabilities.append(float(probability_array[class_index][0][1]))
        elif probability_array.ndim == 2:
            if probability_array.shape[0] == 1:
                probabilities = [float(probability) for probability in probability_array[0]]
            elif probability_array.shape[1] >= 2:
                probabilities = [float(row[1]) for row in probability_array]
            else:
                probabilities = [float(probability) for probability in probability_array.reshape(-1)]
        elif probability_array.ndim == 1:
            probabilities = [float(probability) for probability in probability_array]
        else:
            probabilities = [0.0 for _ in DISTORTION_LABELS]

    result = {label: 0.0 for label in DISTORTION_LABELS}

    if hasattr(classifier_model, "classes_"):
        class_labels = [_normalize_label(cls) for cls in classifier_model.classes_]
        has_named_label_overlap = any(label in result for label in class_labels)

        if has_named_label_overlap:
            for label, probability in zip(class_labels, probabilities):
                if label in result:
                    result[label] = probability
        else:
            for index, label in enumerate(DISTORTION_LABELS):
                if index < len(probabilities):
                    result[label] = probabilities[index]
    else:
        for index, label in enumerate(DISTORTION_LABELS):
            if index < len(probabilities):
                result[label] = probabilities[index]

    sorted_distortions = sorted(result.items(), key=lambda item: item[1], reverse=True)
    top_distortions = sorted_distortions[:3]
    max_probability = sorted_distortions[0][1] if sorted_distortions else 0.0

    if max_probability >= 0.25:
        confidence_label = "Strong Signal"
    elif max_probability >= 0.10:
        confidence_label = "Moderate Signal"
    else:
        confidence_label = "Mild Signal"

    logger.info("Prediction complete: max_probability=%.4f, confidence=%s", max_probability, confidence_label)

    return {
        "probabilities": result,
        "sorted_distortions": sorted_distortions,
        "top_distortions": top_distortions,
        "max_probability": max_probability,
        "confidence_label": confidence_label,
    }


def debug_model_status():
    if classifier_model is None:
        print("Classifier model is None.")
        return

    print("Has estimators:", hasattr(classifier_model, "estimators_"))

    if not hasattr(classifier_model, "estimators_"):
        print("Model is not fitted.")
        return

    print("Number of estimators:", len(classifier_model.estimators_))

    for i, est in enumerate(classifier_model.estimators_):
        try:
            print(
                "Estimator",
                i,
                "| coef shape:",
                est.coef_.shape,
                "| coef sum:",
                est.coef_.sum()
            )
        except Exception as e:
            print("Error reading estimator", i, ":", e)


def debug_prediction_verification():
    test_sentences = [
        "I made one mistake in class, so I am a complete failure.",
        "My friend did not reply quickly; maybe they are upset with me.",
        "The presentation had issues, but I can improve next time.",
    ]

    if classifier_model is None or embedding_model is None:
        print("Cannot run verification: model artifacts are not loaded.")
        return

    for index, sentence in enumerate(test_sentences, start=1):
        print("-" * 80)
        print(f"Test {index}: {sentence}")

        try:
            output = analyze_thought(sentence)
        except Exception as error:
            logger.exception("Verification inference failed on test sentence %d.", index)
            print(f"Inference failed: {error}")
            continue

        probabilities = output.get("probabilities", {})
        top_distortions = output.get("top_distortions", [])
        max_probability = float(output.get("max_probability", 0.0))
        confidence_label = output.get("confidence_label", "Unknown")

        print("Probabilities:")
        for label, value in sorted(probabilities.items(), key=lambda item: item[1], reverse=True):
            print(f"  - {label}: {float(value):.4f}")

        print("Top distortions:", top_distortions)
        print("Confidence:", confidence_label)
        print("Max probability:", f"{max_probability:.4f}")

        all_zero = all(float(value) == 0.0 for value in probabilities.values()) if probabilities else True
        is_sorted = all(
            top_distortions[i][1] >= top_distortions[i + 1][1]
            for i in range(len(top_distortions) - 1)
        )

        print("All probabilities zero:", all_zero)
        print("Top distortions sorted:", is_sorted)
