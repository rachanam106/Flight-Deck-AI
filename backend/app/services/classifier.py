
import re

INTENT_PATTERNS = {
    "SAL-001": [
        r"\b(current|overall|total|show|what is|how much)\b.*\b(sales )?pipeline\b",
        r"\bpipeline\b",
    ],
    "SAL-004": [
        r"\b(top|largest|biggest|highest|most valuable)\b.*\b(deals|opportunities)\b",
        r"\b(top 10|ten largest)\b.*\b(deals|opportunities)\b",
    ],
    "REV-001": [
        r"\b(total|recognized)\b.*\brevenue\b.*\b(this quarter|quarter)\b",
        r"\brevenue\b.*\b(this quarter|quarter to date)\b",
    ],
    "REV-004": [
        r"\b(monthly|month by month)\b.*\brevenue\b",
        r"\brevenue\b.*\b(trend|last 12 months|past 12 months)\b",
    ],
    "BIL-001": [
        r"\b(pending|unbilled)\b.*\b(billing|invoice|work)\b",
        r"\bhow much\b.*\b(billing|invoicing)\b.*\bpending\b",
    ],
    "BIL-002": [
        r"\b(overdue|late|past due)\b.*\b(billing|invoice|invoices|customers)\b",
        r"\b(customers|clients)\b.*\b(highest|most)\b.*\boverdue\b",
    ],
}


def classify_question(question: str):
    normalized = re.sub(r"\s+", " ", question.lower()).strip()

    for query_id, patterns in INTENT_PATTERNS.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            return {
                "query_id": query_id,
                "confidence": 0.90,
            }

    return {
        "query_id": None,
        "confidence": 0.0,
    }
