"""
FFmpeg wrapper module.

All video and audio processing goes through this module.
Provides functions for trimming, scaling, concatenating, audio mixing,
subtitle burning, and audio normalization via FFmpeg/FFprobe CLI tools.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# -- path bootstrap ----------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Internal helpers
# ============================================================================

def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess:
    """Run an ffmpeg command with standard flags and error handling.

    Args:
        args: Arguments to pass *after* the ``ffmpeg`` binary name.
              Do **not** include ``ffmpeg`` itself.

    Returns:
        The completed process on success.

    Raises:
        RuntimeError: If ffmpeg exits with a non-zero return code.
    """
    cmd = ["ffmpeg", "-hide_banner", "-y"] + args
    logger.debug("FFmpeg command: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg stderr:\n%s", result.stderr)
        raise RuntimeError(
            f"FFmpeg failed (rc={result.returncode}): {result.stderr[:500]}"
        )

    return result


def _run_ffprobe(args: list[str]) -> subprocess.CompletedProcess:
    """Run an ffprobe command with error handling.

    Args:
        args: Arguments to pass *after* the ``ffprobe`` binary name.

    Returns:
        The completed process on success.

    Raises:
        RuntimeError: If ffprobe exits with a non-zero return code.
    """
    cmd = ["ffprobe", "-hide_banner"] + args
    logger.debug("FFprobe command: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFprobe stderr:\n%s", result.stderr)
        raise RuntimeError(
            f"FFprobe failed (rc={result.returncode}): {result.stderr[:500]}"
        )

    return result


def _escape_srt_path(srt_path: Path) -> str:
    """Escape an SRT file path for the FFmpeg subtitles filter on Windows.

    The ``subtitles`` filter uses libass which expects forward-slashes or
    double-backslashes.  Colons in Windows drive letters (``C:``) must also
    be escaped with a backslash.

    Args:
        srt_path: Absolute path to the ``.srt`` file.

    Returns:
        A properly escaped string suitable for the ``subtitles=`` filter.
    """
    # Convert to forward slashes, then escape the colon after drive letter
    escaped = str(srt_path).replace("\\", "/")
    # Escape the colon in the drive letter (e.g. C: -> C\\:)
    if len(escaped) >= 2 and escaped[1] == ":":
        escaped = escaped[0] + "\\:" + escaped[2:]
    return escaped


# ============================================================================
# Public API
# ============================================================================

def verify_ffmpeg() -> bool:
    """Check that ``ffmpeg`` and ``ffprobe`` are available on PATH.

    Logs the version string for each tool.

    Returns:
        ``True`` if both tools are found, ``False`` otherwise.
    """
    ok = True

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            logger.error("%s not found on PATH", tool)
            ok = False
            continue

        try:
            result = subprocess.run(
                [tool, "-version"],
                capture_output=True,
                text=True,
            )
            # First line of -version output contains the version string
            version_line = result.stdout.strip().split("\n")[0]
            logger.info("%s found: %s", tool, version_line)
        except Exception as exc:
            logger.error("Failed to run %s -version: %s", tool, exc)
            ok = False

    return ok


def get_duration(file_path: Path) -> float:
    """Get the duration of a media file in seconds.

    Args:
        file_path: Path to the audio or video file.

    Returns:
        Duration in seconds as a float.
    """
    file_path = Path(file_path)
    result = _run_ffprobe([
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(file_path),
    ])

    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    logger.debug("Duration of %s: %.2fs", file_path.name, duration)
    return duration


def get_video_info(file_path: Path) -> dict:
    """Get detailed information about a video file.

    Args:
        file_path: Path to the video file.

    Returns:
        Dictionary with keys: ``width``, ``height``, ``duration``,
        ``codec``, ``fps``.
    """
    file_path = Path(file_path)
    result = _run_ffprobe([
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-select_streams", "v:0",
        str(file_path),
    ])

    data = json.loads(result.stdout)

    stream = data["streams"][0] if data.get("streams") else {}
    fmt = data.get("format", {})

    # Parse frame rate from r_frame_rate (e.g. "30/1")
    fps = 0.0
    r_frame_rate = stream.get("r_frame_rate", "0/1")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 0.0
    else:
        fps = float(r_frame_rate)

    info = {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "duration": float(fmt.get("duration", stream.get("duration", 0))),
        "codec": stream.get("codec_name", "unknown"),
        "fps": round(fps, 2),
    }

    logger.info(
        "Video info for %s: %dx%d, %.2fs, %s @ %.2f fps",
        file_path.name,
        info["width"],
        info["height"],
        info["duration"],
        info["codec"],
        info["fps"],
    )
    return info


def trim_video(
    input_path: Path,
    output_path: Path,
    start: float,
    duration: float,
) -> Path:
    """Trim a video clip using fast input seeking.

    Places ``-ss`` *before* ``-i`` for fast keyframe seeking and applies
    ``-t`` to limit duration.

    Args:
        input_path:  Source video file.
        output_path: Destination for the trimmed clip.
        start:       Start time in seconds.
        duration:    Desired clip length in seconds.

    Returns:
        The *output_path* on success.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Trimming %s — start=%.2fs, duration=%.2fs",
        input_path.name, start, duration,
    )

    _run_ffmpeg([
        "-ss", str(start),
        "-i", str(input_path),
        "-t", str(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_path),
    ])

    logger.info("Trimmed video saved to %s", output_path.name)
    return output_path


def loop_video(
    input_path: Path,
    output_path: Path,
    target_duration: float,
) -> Path:
    """Loop a short clip so it fills *target_duration* seconds.

    Uses ``-stream_loop`` to repeat and ``-t`` to cut at the target.

    Args:
        input_path:      Short source video.
        output_path:     Destination for the looped video.
        target_duration: Desired total duration in seconds.

    Returns:
        The *output_path* on success.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Looping %s to %.2fs",
        input_path.name, target_duration,
    )

    _run_ffmpeg([
        "-stream_loop", "-1",
        "-i", str(input_path),
        "-t", str(target_duration),
        "-c", "copy",
        str(output_path),
    ])

    logger.info("Looped video saved to %s", output_path.name)
    return output_path


def scale_and_crop(
    input_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    """Scale a video to fill the target frame and center-crop the overflow.

    Uses ``scale=w:h:force_original_aspect_ratio=increase`` followed by
    ``crop=w:h`` so the output is exactly *width* × *height* with no
    letterboxing.

    Args:
        input_path:  Source video.
        output_path: Destination for the scaled/cropped video.
        width:       Target width in pixels (default 1080).
        height:      Target height in pixels (default 1920).

    Returns:
        The *output_path* on success.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )

    logger.info(
        "Scaling & cropping %s to %dx%d",
        input_path.name, width, height,
    )

    _run_ffmpeg([
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        str(output_path),
    ])

    logger.info("Scaled video saved to %s", output_path.name)
    return output_path


def concat_videos(
    input_paths: list[Path],
    output_path: Path,
) -> Path:
    """Concatenate multiple video files using the concat demuxer.

    Writes a temporary file list and re-encodes to ensure consistent
    output with ``libx264`` / ``yuv420p``.

    Args:
        input_paths: Ordered list of video files to concatenate.
        output_path: Destination for the joined video.

    Returns:
        The *output_path* on success.

    Raises:
        ValueError: If *input_paths* is empty.
    """
    if not input_paths:
        raise ValueError("input_paths must not be empty")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Concatenating %d clips -> %s", len(input_paths), output_path.name)

    import os
    # Build the concat demuxer file list in a temp file
    tmp_fd, tmp_list = tempfile.mkstemp(suffix=".txt", prefix="ffconcat_")
    os.close(tmp_fd)
    try:
        with open(tmp_list, "w", encoding="utf-8") as fh:
            for p in input_paths:
                # Escape single quotes for the concat demuxer
                safe = str(Path(p).resolve()).replace("'", "'\\''")
                fh.write(f"file '{safe}'\n")

        _run_ffmpeg([
            "-f", "concat",
            "-safe", "0",
            "-i", tmp_list,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ])
    finally:
        Path(tmp_list).unlink(missing_ok=True)

    logger.info("Concatenated video saved to %s", output_path.name)
    return output_path


def mix_audio(
    video_path: Path,
    voice_path: Path,
    music_path: Path,
    output_path: Path,
    voice_vol: float = 1.0,
    music_vol: float = 0.05,
) -> Path:
    """Mix voice-over and background music onto a video.

    The music track is looped to cover the full video length.
    Volume levels are applied via the ``volume`` filter before merging
    with ``amix``.

    Args:
        video_path: Source video (may or may not already have audio).
        voice_path: Voice-over audio file.
        music_path: Background music audio file.
        output_path: Destination for the final video.
        voice_vol:  Volume multiplier for voice (default 1.0).
        music_vol:  Volume multiplier for music (default 0.1).

    Returns:
        The *output_path* on success.
    """
    video_path = Path(video_path)
    voice_path = Path(voice_path)
    music_path = Path(music_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Mixing audio — voice_vol=%.2f, music_vol=%.2f",
        voice_vol, music_vol,
    )

    # Get video duration to limit the music loop
    vid_duration = get_duration(video_path)

    # filter_complex:
    #   [1] voice -> volume adjust -> split -> [v_audio1], [v_audio2]
    #   [2] music loop -> volume adjust -> [m_audio]
    #   Apply sidechaincompress on music triggered by voice -> [ducked_music]
    #   amix the voice and ducked music -> [mixed]
    filter_complex = (
        f"[1:a]volume={voice_vol},asplit=2[v_audio1][v_audio2];"
        f"[2:a]aloop=loop=-1:size=2e+09,atrim=0:{vid_duration},"
        f"volume={music_vol}[m_audio];"
        f"[m_audio][v_audio1]sidechaincompress=threshold=0.12:ratio=4.5:attack=50:release=300[ducked_music];"
        f"[v_audio2][ducked_music]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
    )

    _run_ffmpeg([
        "-i", str(video_path),
        "-i", str(voice_path),
        "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[mixed]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        str(output_path),
    ])

    logger.info("Audio-mixed video saved to %s", output_path.name)
    return output_path


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    font_name: str = "Cinzel",
    font_size: int = 24,
    margin_v: int = 60,
    fonts_dir: Path | None = None,
    back_color: str = "&H80800000",
) -> Path:
    """Burn SRT subtitles into a video with styled text.

    Renders white bold text with a black outline and semi-transparent
    opaque box background, positioned at the bottom center of the frame.
    Uses Cinzel Bold by default for a premium cinematic look.

    On Windows the SRT path is escaped to use forward slashes and the
    drive-letter colon is backslash-escaped so libass can parse it.

    Args:
        video_path:  Source video.
        srt_path:    Path to the ``.srt`` subtitle file.
        output_path: Destination for the subtitled video.
        font_name:   Font family name (default ``Cinzel``).
        font_size:   Font size in pixels (default 26).
        margin_v:    Vertical margin from bottom in pixels (default 60).
        fonts_dir:   Optional directory containing custom ``.ttf``/``.otf``
                     font files.  Passed as ``fontsdir=`` to the FFmpeg
                     subtitles filter so libass can locate them.

    Returns:
        The *output_path* on success.
    """
    video_path = Path(video_path)
    srt_path = Path(srt_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    escaped_srt = _escape_srt_path(srt_path.resolve())

    # force_style: Bold Cinzel, white text, yellow highlight, opaque box
    force_style = (
        f"FontName={font_name},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"SecondaryColour=&H00000000,"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H40000000,"
        f"BorderStyle=1,"
        f"Outline=2.5,"
        f"Shadow=1,"
        f"Bold=1,"
        f"Alignment=2,"
        f"MarginV={margin_v}"
    )

    if fonts_dir is not None:
        escaped_fonts_dir = str(fonts_dir).replace('\\', '/').replace(':', '\\:')
        vf = f"subtitles='{escaped_srt}':fontsdir='{escaped_fonts_dir}':force_style='{force_style}'"
    else:
        vf = f"subtitles='{escaped_srt}':force_style='{force_style}'"

    logger.info(
        "Burning subtitles from %s with font=%s size=%d",
        srt_path.name, font_name, font_size,
    )

    _run_ffmpeg([
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "copy",
        str(output_path),
    ])

    logger.info("Subtitled video saved to %s", output_path.name)
    return output_path


def normalize_audio(
    input_path: Path,
    output_path: Path,
) -> Path:
    """Normalize audio levels using the EBU R128 ``loudnorm`` filter.

    Runs a two-pass approach:
      1. **Analysis pass** — measures integrated loudness, true peak, and
         loudness range.
      2. **Encoding pass** — applies linear normalization using the
         measured values for higher quality than single-pass.

    Args:
        input_path:  Source audio/video file.
        output_path: Destination for the normalized file.

    Returns:
        The *output_path* on success.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Normalizing audio for %s (two-pass loudnorm)", input_path.name)

    # ---- Pass 1: analysis ----
    analysis_result = _run_ffmpeg([
        "-i", str(input_path),
        "-af", "loudnorm=print_format=json",
        "-f", "null",
        "-",
    ])

    # The loudnorm JSON block is printed to stderr
    stderr_text = analysis_result.stderr

    # Extract the JSON object from stderr
    json_start = stderr_text.rfind("{")
    json_end = stderr_text.rfind("}") + 1

    # Determine proper codec based on output path extension
    codec_args = ["-c:a", "aac", "-b:a", "192k"]
    if output_path.suffix.lower() == ".mp3":
        codec_args = ["-c:a", "libmp3lame", "-q:a", "2"]

    if json_start == -1 or json_end == 0:
        logger.warning(
            "Could not parse loudnorm analysis — falling back to single-pass"
        )
        _run_ffmpeg([
            "-i", str(input_path),
            "-af", "loudnorm"
        ] + codec_args + [
            str(output_path),
        ])
        logger.info("Audio normalized (single-pass) -> %s", output_path.name)
        return output_path

    stats = json.loads(stderr_text[json_start:json_end])

    measured_i = stats.get("input_i", "-24.0")
    measured_tp = stats.get("input_tp", "-2.0")
    measured_lra = stats.get("input_lra", "7.0")
    measured_thresh = stats.get("input_thresh", "-34.0")
    target_offset = stats.get("target_offset", "0.0")

    logger.debug(
        "Loudnorm analysis: I=%s, TP=%s, LRA=%s, thresh=%s, offset=%s",
        measured_i, measured_tp, measured_lra, measured_thresh, target_offset,
    )

    # ---- Pass 2: apply normalization ----
    loudnorm_filter = (
        f"loudnorm=I=-16:TP=-1.5:LRA=11:"
        f"measured_I={measured_i}:"
        f"measured_TP={measured_tp}:"
        f"measured_LRA={measured_lra}:"
        f"measured_thresh={measured_thresh}:"
        f"offset={target_offset}:"
        f"linear=true:print_format=summary"
    )

    _run_ffmpeg([
        "-i", str(input_path),
        "-af", loudnorm_filter
    ] + codec_args + [
        str(output_path),
    ])

    logger.info("Audio normalized (two-pass) -> %s", output_path.name)
    return output_path


# ============================================================================
# CLI entry point
# ============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    print("=" * 60)
    print("FFmpeg Utility — Verification")
    print("=" * 60)

    if verify_ffmpeg():
        print("\n[OK]  FFmpeg and FFprobe are available and working.")
    else:
        print("\n[FAIL]  FFmpeg or FFprobe is missing. Install from https://ffmpeg.org/")
        sys.exit(1)
