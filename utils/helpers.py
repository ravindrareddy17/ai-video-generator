"""
General-purpose helper utilities for the AI Video Generator V2 pipeline.

Provides:
    - save_json / load_json  — JSON file I/O with UTF-8 encoding
    - clean_text             — whitespace & unicode normalisation
    - clean_directory        — wipe files inside a directory
    - format_duration        — human-readable mm:ss strings
    - slugify                — convert arbitrary text to a safe filename
"""

import json
import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

# ── project imports ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger(__name__)


# ─── JSON helpers ────────────────────────────────────────────────────

def save_json(data: dict | list, path: Path) -> None:
    """Write *data* as pretty-printed JSON to *path*.

    Parent directories are created automatically.

    Args:
        data: Serialisable dict or list.
        path: Destination file (will be overwritten if it exists).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    logger.debug("Saved JSON (%d bytes) → %s", path.stat().st_size, path)


def extract_json_from_llm(raw_text: str) -> dict | list:
    """Robustly extract and parse JSON from raw LLM text outputs, handling thinking tags and markdown code blocks."""
    if not raw_text:
        raise ValueError("Empty response from LLM")
        
    clean = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    clean = re.sub(r'```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'```\s*', '', clean).strip()

    match = re.search(r'(\{.*\}|\[.*\])', clean, re.DOTALL)
    if match:
        clean = match.group(1)
        
    return json.loads(clean)

def load_json(path: Path) -> dict | list:
    """Read and return JSON content from *path*.

    Args:
        path: Source JSON file.

    Returns:
        Parsed dict or list.

    Raises:
        FileNotFoundError: If *path* does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data: Any = json.load(fh)

    if not isinstance(data, (dict, list)):
        raise TypeError(
            f"Expected dict or list at top level, got {type(data).__name__}"
        )

    logger.debug("Loaded JSON (%d bytes) ← %s", path.stat().st_size, path)
    return data


# ─── Text helpers ────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalise unicode and collapse whitespace.

    Steps:
        1. NFC unicode normalisation (compose diacritics).
        2. Replace any run of whitespace (including newlines) with a single space.
        3. Strip leading/trailing whitespace.

    Args:
        text: Raw input string.

    Returns:
        Cleaned string.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text: str) -> str:
    """Convert arbitrary text into a filesystem-safe slug.

    Steps:
        1. NFKD unicode normalisation (decompose).
        2. Strip non-ASCII characters.
        3. Lowercase.
        4. Replace any non-alphanumeric character with a hyphen.
        5. Collapse consecutive hyphens and strip edge hyphens.

    Args:
        text: Human-readable string (title, label, etc.).

    Returns:
        Lowercase, hyphen-separated slug safe for filenames.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text


# ─── Filesystem helpers ─────────────────────────────────────────────

def clean_directory(path: Path) -> None:
    """Remove every *file* inside *path* without deleting the directory itself.

    Subdirectories are left untouched.  If *path* does not exist it is
    created as an empty directory.

    Args:
        path: Directory to clean.
    """
    path = Path(path)

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("Created empty directory: %s", path)
        return

    removed = 0
    for item in path.iterdir():
        if item.is_file():
            item.unlink()
            removed += 1

    logger.info("Removed %d file(s) from %s", removed, path)


# ─── Formatting helpers ─────────────────────────────────────────────

def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Examples:
        45.3  → '45s'
        83.7  → '1m 23s'
        3661  → '61m 1s'

    Args:
        seconds: Non-negative duration in seconds.

    Returns:
        Formatted string like '1m 23s' or '45s'.
    """
    if seconds < 0:
        raise ValueError("Duration must be non-negative")

    total = int(seconds)
    mins, secs = divmod(total, 60)

    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


# ──────────────────────────────────────────────────────────────────────
# Demo / self-test
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    # ── save_json / load_json ────────────────────────────────────────
    tmp_dir = Path(tempfile.mkdtemp())
    json_path = tmp_dir / "test.json"

    sample = {"title": "Héllo Wörld", "tags": ["AI", "video"], "count": 42}
    save_json(sample, json_path)
    loaded = load_json(json_path)
    assert loaded == sample, f"Round-trip failed: {loaded}"
    logger.info("✓ save_json / load_json round-trip passed")

    # ── load_json — missing file ─────────────────────────────────────
    try:
        load_json(tmp_dir / "nope.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        logger.info("✓ load_json raises FileNotFoundError correctly")

    # ── clean_text ───────────────────────────────────────────────────
    dirty = "  Hello\t\n  world   café  "
    assert clean_text(dirty) == "Hello world café"
    logger.info("✓ clean_text passed")

    # ── slugify ──────────────────────────────────────────────────────
    assert slugify("Hello World! — Part 2") == "hello-world-part-2"
    assert slugify("  --edge cases-- ") == "edge-cases"
    assert slugify("café résumé") == "cafe-resume"
    logger.info("✓ slugify passed")

    # ── format_duration ──────────────────────────────────────────────
    assert format_duration(45.3) == "45s"
    assert format_duration(83.7) == "1m 23s"
    assert format_duration(0) == "0s"
    assert format_duration(3661) == "61m 1s"
    logger.info("✓ format_duration passed")

    # ── clean_directory ──────────────────────────────────────────────
    test_dir = tmp_dir / "clean_test"
    test_dir.mkdir()
    (test_dir / "a.txt").write_text("a")
    (test_dir / "b.txt").write_text("b")
    sub = test_dir / "subdir"
    sub.mkdir()
    (sub / "keep.txt").write_text("keep")

    clean_directory(test_dir)
    remaining = list(test_dir.iterdir())
    assert len(remaining) == 1 and remaining[0].is_dir(), (
        f"Expected only subdir, got {remaining}"
    )
    logger.info("✓ clean_directory passed (files removed, subdir kept)")

    # ── clean_directory — non-existent path ──────────────────────────
    new_dir = tmp_dir / "brand_new"
    clean_directory(new_dir)
    assert new_dir.is_dir()
    logger.info("✓ clean_directory creates missing directory")

    # ── cleanup ──────────────────────────────────────────────────────
    import shutil
    shutil.rmtree(tmp_dir)
    logger.info("All helpers tests passed ✓")
