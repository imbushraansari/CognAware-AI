import re


RISK_KEYWORDS = {
	"high": {
		"suicide",
		"kill myself",
		"end my life",
		"want to die",
		"self harm",
		"cut myself",
		"no reason to live",
	},
	"moderate": {
		"hopeless",
		"worthless",
		"cannot go on",
		"life is pointless",
		"i am done",
		"nobody cares",
	},
}


SUPPORT_MESSAGE = (
	"If you feel unsafe or overwhelmed, please reach out to a trusted person or local crisis support immediately. "
	"You deserve help and support."
)


def _contains_keyword(text: str, keyword: str) -> bool:
	normalized_text = re.sub(r"\s+", " ", text.lower()).strip()
	normalized_keyword = re.sub(r"\s+", " ", keyword.lower()).strip()
	return normalized_keyword in normalized_text


def assess_safety_risk(thought_text: str) -> dict:
	text = (thought_text or "").strip()
	if not text:
		return {
			"risk_level": "none",
			"requires_alert": False,
			"matched_keywords": [],
			"support_message": "",
		}

	matched_high = [keyword for keyword in RISK_KEYWORDS["high"] if _contains_keyword(text, keyword)]
	if matched_high:
		return {
			"risk_level": "high",
			"requires_alert": True,
			"matched_keywords": sorted(matched_high),
			"support_message": SUPPORT_MESSAGE,
		}

	matched_moderate = [keyword for keyword in RISK_KEYWORDS["moderate"] if _contains_keyword(text, keyword)]
	if matched_moderate:
		return {
			"risk_level": "moderate",
			"requires_alert": True,
			"matched_keywords": sorted(matched_moderate),
			"support_message": SUPPORT_MESSAGE,
		}

	return {
		"risk_level": "none",
		"requires_alert": False,
		"matched_keywords": [],
		"support_message": "",
	}
