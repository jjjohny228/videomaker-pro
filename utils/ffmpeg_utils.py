import subprocess
import json
import os
from typing import Dict, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class FFmpegUtils:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def run_command(self, command: list) -> subprocess.CompletedProcess:
        """Выполняет команду FFmpeg"""
        logger.debug(f"Выполнение команды FFmpeg: {' '.join(command)}")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка выполнения команды FFmpeg: {e.stderr}")
            raise

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Получает информацию о видео

        Args:
            video_path: Путь к видео файлу

        Returns:
            Словарь с информацией о видео
        """
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-hide_banner",
            "-loglevel", "error"
        ]

        try:
            # FFmpeg выводит информацию в stderr для команды -i
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr

            # Извлекаем размеры видео
            width_height_match = re.search(r"Stream.*Video.*\s(\d+)x(\d+)", output)
            if width_height_match:
                width = int(width_height_match.group(1))
                height = int(width_height_match.group(2))
            else:
                width, height = 0, 0

            # Извлекаем длительность видео
            duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                duration = hours * 3600 + minutes * 60 + seconds
            else:
                duration = 0.0

            # Извлекаем FPS
            fps_match = re.search(r"(\d+(?:\.\d+)?) fps", output)
            fps = float(fps_match.group(1)) if fps_match else 30.0

            return {
                "width": width,
                "height": height,
                "duration": duration,
                "fps": fps
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о видео: {str(e)}")
            return {
                "width": 1920,
                "height": 1080,
                "duration": 60.0,
                "fps": 30.0
            }

    def get_duration(self, media_path: str) -> float:
        """
        Получает длительность медиа файла

        Args:
            media_path: Путь к медиа файлу

        Returns:
            Длительность в секундах
        """
        cmd = [
            self.ffmpeg_path,
            "-i", media_path,
            "-hide_banner",
            "-loglevel", "error"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr

            duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                return hours * 3600 + minutes * 60 + seconds
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения длительности медиа: {str(e)}")
            return 0.0

    def create_transition(self, clip1: str, clip2: str, output: str,
                          transition_type: str = "fade", duration: float = 0.5) -> str:
        """
        Создает переход между двумя клипами

        Args:
            clip1: Путь к первому клипу
            clip2: Путь ко второму клипу
            output: Путь к выходному файлу
            transition_type: Тип перехода (fade, wipe, slide)
            duration: Длительность перехода в секундах

        Returns:
            Путь к выходному файлу
        """
        # Получаем длительность первого клипа
        clip1_info = self.get_video_info(clip1)
        clip1_duration = clip1_info["duration"]

        # Создаем фильтр для перехода
        if transition_type == "fade":
            filter_complex = (
                f"[0:v]trim=0:{clip1_duration - duration},setpts=PTS-STARTPTS[v0];"
                f"[0:v]trim={clip1_duration - duration}:{clip1_duration},setpts=PTS-STARTPTS[v1];"
                f"[1:v]trim=0:{duration},setpts=PTS-STARTPTS[v2];"
                f"[1:v]trim={duration},setpts=PTS-STARTPTS[v3];"
                f"[v1][v2]xfade=transition=fade:duration={duration}:offset=0[xf];"
                f"[v0][xf][v3]concat=n=3:v=1:a=0[outv]"
            )
        elif transition_type == "wipe":
            filter_complex = (
                f"[0:v]trim=0:{clip1_duration - duration},setpts=PTS-STARTPTS[v0];"
                f"[0:v]trim={clip1_duration - duration}:{clip1_duration},setpts=PTS-STARTPTS[v1];"
                f"[1:v]trim=0:{duration},setpts=PTS-STARTPTS[v2];"
                f"[1:v]trim={duration},setpts=PTS-STARTPTS[v3];"
                f"[v1][v2]xfade=transition=wipeleft:duration={duration}:offset=0[xf];"
                f"[v0][xf][v3]concat=n=3:v=1:a=0[outv]"
            )
        elif transition_type == "slide":
            filter_complex = (
                f"[0:v]trim=0:{clip1_duration - duration},setpts=PTS-STARTPTS[v0];"
                f"[0:v]trim={clip1_duration - duration}:{clip1_duration},setpts=PTS-STARTPTS[v1];"
                f"[1:v]trim=0:{duration},setpts=PTS-STARTPTS[v2];"
                f"[1:v]trim={duration},setpts=PTS-STARTPTS[v3];"
                f"[v1][v2]xfade=transition=slideleft:duration={duration}:offset=0[xf];"
                f"[v0][xf][v3]concat=n=3:v=1:a=0[outv]"
            )
        else:
            # По умолчанию используем fade
            filter_complex = (
                f"[0:v]trim=0:{clip1_duration - duration},setpts=PTS-STARTPTS[v0];"
                f"[0:v]trim={clip1_duration - duration}:{clip1_duration},setpts=PTS-STARTPTS[v1];"
                f"[1:v]trim=0:{duration},setpts=PTS-STARTPTS[v2];"
                f"[1:v]trim={duration},setpts=PTS-STARTPTS[v3];"
                f"[v1][v2]xfade=transition=fade:duration={duration}:offset=0[xf];"
                f"[v0][xf][v3]concat=n=3:v=1:a=0[outv]"
            )

        # Выполняем команду FFmpeg
        cmd = [
            self.ffmpeg_path,
            "-i", clip1,
            "-i", clip2,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "22",
            "-y",
            output
        ]

        self.run_command(cmd)
        return output
