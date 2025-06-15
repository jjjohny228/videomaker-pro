import os
import subprocess
import logging
import time
from core.config import Config
from database.functions import get_active_assembly_ai_api_key

from utils.subtitle_utils import (
    generate_subtitles,
    parse_srt,
    generate_ass_subtitles_from_segments
)

logger = logging.getLogger(__name__)

class CaptionProcessor:
    def __init__(self, brand_kit):
        self.brand_kit = brand_kit
        self.caption_specification = brand_kit.caption_config
        self.temp_dir = Config.TEMP_FOLDER

    def add_captions(self, audio_path: str, video_path: str) -> str:
        """
        Transcribes audio, generates styled ASS subtitles, and adds them to the video.
        """
        # Transcribe audio to SRT
        srt_file = os.path.join(self.temp_dir, f"{int(time.time())}_srt_temp.srt")
        language_code = self.brand_kit.language_code
        assemblyai_api_key = get_active_assembly_ai_api_key()
        generate_subtitles(
            audio_file_path=audio_path,
            language_code=language_code,
            output_file=srt_file,
            assemblyai_api_key=assemblyai_api_key
        )

        # Parse SRT to segments
        segments = parse_srt(srt_file)

        # Prepare ASS styling
        font = self.caption_specification.font
        font_size = self.caption_specification.font_size
        color = self.caption_specification.font_color
        stroke_width = self.caption_specification.stroke_width
        stroke_color = self.caption_specification.stroke_color
        alignment = self._get_alignment_from_position(self.caption_specification.position)
        margin_v = self._get_margin_v(font_size, self.caption_specification.position)
        max_words_per_line = self.caption_specification.max_words_per_line

        # Generate ASS file
        ass_file = os.path.join(self.temp_dir, f"{int(time.time())}_subtitles.ass")
        generate_ass_subtitles_from_segments(
            segments,
            ass_file,
            font=font,
            font_size=font_size,
            color=color,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            alignment=alignment,
            margin_v=margin_v,
            max_words_per_line=max_words_per_line
        )

        # Add subtitles to video
        output_file = os.path.join(self.temp_dir, f"{int(time.time())}_captioned.mp4")
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"ass={ass_file}",
            "-c:v", Config.VIDEO_CODEC,
            "-c:a", "copy",
            "-y",
            output_file
        ]
        subprocess.run(cmd, check=True)
        os.remove(srt_file)
        os.remove(ass_file)
        return output_file

    @staticmethod
    def _get_alignment_from_position(position: str) -> int:
        """
        Converts position string to ASS alignment number.
        """
        mapping = {
            "bottom_center": 2,
            "center": 5
        }
        return mapping.get(position, 2)

    @staticmethod
    def _get_margin_v(font_size: int, position: str) -> int:
        """
        Calculates vertical margin for subtitles based on font size and position.
        """
        if position == "center":
            return 20
        elif position == "bottom_center":
            return int(font_size * 2.5)
