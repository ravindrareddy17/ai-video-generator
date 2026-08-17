import hashlib
import re

def generate_fingerprint(text: str) -> str:
    """Generate normalized SHA-256 fingerprint for deduplication."""
    clean = re.sub(r'[^\w\s]', '', str(text)).strip().lower()
    words = sorted(set([w for w in clean.split() if len(w) > 3]))
    normalized = " ".join(words)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]

def check_topic_duplicate(topic: str, existing_fingerprints: list[str]) -> bool:
    """Check if topic fingerprint matches any existing historical fingerprints."""
    fp = generate_fingerprint(topic)
    return fp in existing_fingerprints

def generate_all_fingerprints(topic: str, story: str, claim: str, title: str, hook: str) -> dict:
    """Generate 5 distinct fingerprints to block duplicate concepts, stories, claims, titles, and hooks."""
    return {
        "topic_fingerprint": generate_fingerprint(topic),
        "story_fingerprint": generate_fingerprint(story),
        "claim_fingerprint": generate_fingerprint(claim),
        "title_fingerprint": generate_fingerprint(title),
        "hook_fingerprint": generate_fingerprint(hook)
    }
