import os
import re
from typing import Dict, Any, List
import logging
import subprocess

from utils.subtitle_utils import generate_ass_subtitles, generate_typewriter_effect

logger = logging.getLogger(__name__)


class CaptionProcessor:
    def __init__(self, config):
        self.config = config

    def add_captions(self, video_path: str, script: str, caption_specs: Dict[str, Any], temp_dir: str) -> str:
        """
        Добавляет субтитры к видео

        Args:
            video_path: Путь к видео
            script: Текст скрипта
            caption_specs: Настройки субтитров
            temp_dir: Временная директория

        Returns:
            Путь к видео с субтитрами
        """
        output_file = os.path.join(temp_dir, "captioned.mp4")

        # Разбиваем скрипт на предложения
        sentences = self._split_into_sentences(script)

        # Создаем файл субтитров
        subtitle_file = os.path.join(temp_dir, "subtitles.ass")

        # Получаем длительность видео
        cmd = [
            self.config.ffmpeg_path,
            "-i", video_path,
            "-hide_banner",
            "-loglevel", "error"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr

        duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = float(duration_match.group(3))
            duration = hours * 3600 + minutes * 60 + seconds
        else:
            duration = 0.0

        # Генерируем субтитры
        generate_ass_subtitles(
            sentences,
            subtitle_file,
            duration,
            font=caption_specs.get("font", "Arial"),
            font_size=caption_specs.get("font_size", 24),
            color=caption_specs.get("color", "&HFFFFFF"),
            stroke_width=caption_specs.get("stroke", 2),
            stroke_color=caption_specs.get("stroke_color", "&H000000"),
            alignment=caption_specs.get("position", 2),
            max_words_per_line=caption_specs.get("max_words_per_line", 7)
        )

        # Добавляем субтитры к видео
        cmd = [
            self.config.ffmpeg_path,
            "-i", video_path,
            "-vf", f"ass={subtitle_file}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "22",
            "-c:a", "copy",
            "-y",
            output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def _split_into_sentences(self, text: str) -> List[str]:
        """Разбивает текст на предложения"""
        # Простой алгоритм разделения на предложения
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
