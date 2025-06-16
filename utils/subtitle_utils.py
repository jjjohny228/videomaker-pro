import os
import re
from typing import List

import assemblyai as aai

def generate_subtitles(
    audio_file_path: str,
    language_code: str,
    output_file: str,
    assemblyai_api_key: str
) -> str:
    """
    Transcribes audio to SRT subtitles using AssemblyAI.
    """
    aai.settings.api_key = assemblyai_api_key
    aai.settings.base_url = "https://api.eu.assemblyai.com"
    if not aai.settings.api_key:
        raise ValueError("ASSEMBLYAI_API_KEY is required")
    config = aai.TranscriptionConfig(language_code=language_code)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_file_path)
    srt_subtitles = transcript.export_subtitles_srt()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(srt_subtitles)
    return output_file

def parse_srt(srt_path: str) -> List[dict]:
    """
    Parses SRT file and returns list of dicts: {'start': float, 'end': float, 'text': str}
    """
    segments = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(
        r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\d+\n|\Z)",
        re.MULTILINE
    )
    for match in pattern.finditer(content):
        _, start, end, text = match.groups()
        text = text.replace('\n', ' ').strip()
        segments.append({
            "start": srt_time_to_seconds(start),
            "end": srt_time_to_seconds(end),
            "text": text
        })
    return segments


def srt_time_to_seconds(time_str):
    time_str = time_str.replace(',', '.')

    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])

    seconds_with_ms = float(parts[2])

    total_seconds = hours * 3600 + minutes * 60 + seconds_with_ms
    return total_seconds

def format_time(seconds: float) -> str:
    """Правильно форматирует время для ASS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def generate_ass_subtitles_from_segments(
    segments: List[dict],
    output_file: str,
    font: str,
    font_size: int,
    color: str,
    stroke_width: int,
    stroke_color: str,
    alignment: int,
    margin_v: int,
    max_words_per_line: int
) -> str:
    """
    Generates ASS subtitles from parsed SRT segments.
    """
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},&H00{color},&H00FFFFFF,{stroke_color},&H00000000,0,0,0,0,100,100,0,0,1,{stroke_width},0,{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    for seg in segments:
        words = seg["text"].split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words_per_line:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))
        text = "\\N".join(lines)
        start = format_time(seg["start"])
        end = format_time(seg["end"])
        dialogue_line = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
        ass_content += dialogue_line

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_file
