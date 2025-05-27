import os
import subprocess
from typing import Dict, Any, Optional
import logging
import tempfile

from utils.ffmpeg_utils import FFmpegUtils

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, config):
        self.config = config
        self.ffmpeg = FFmpegUtils(config.ffmpeg_path)

    def adjust_audio_speed(self, audio_path: str, speed: float, output_path: str = "") -> str:
        """
        Изменяет скорость аудио

        Args:
            audio_path: Путь к аудио файлу
            speed: Коэффициент скорости (1.0 = нормальная)
            output_path: Путь к выходному файлу

        Returns:
            Путь к обработанному аудио файлу
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix=".mp3")

        cmd = [
            "-i", audio_path,
            "-filter:a", f"atempo={speed}",
            "-y", output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path

    def mix_audio_with_music(self, voice_path: str, music_path: str,
                             music_volume: float = 0.2, output_path: str = "") -> str:
        """
        Смешивает голос с фоновой музыкой

        Args:
            voice_path: Путь к файлу с голосом
            music_path: Путь к файлу с музыкой
            music_volume: Громкость музыки (0.0 - 1.0)
            output_path: Путь к выходному файлу

        Returns:
            Путь к смешанному аудио файлу
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix=".mp3")

        # Получаем длительность голоса
        voice_duration = self.ffmpeg.get_duration(voice_path)
        music_duration = self.ffmpeg.get_duration(music_path)

        # Формируем команду для смешивания аудио
        if music_duration < voice_duration:
            # Музыка короче голоса, нужно зациклить и обрезать
            cmd = [
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex",
                f"[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[a1];[a1]atrim=0:{voice_duration}[a2];[0:a][a2]amix=inputs=2:duration=first",
                "-y", output_path
            ]
        else:
            # Музыка длиннее голоса, просто обрезаем музыку
            cmd = [
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex",
                f"[1:a]volume={music_volume},atrim=0:{voice_duration}[a1];[0:a][a1]amix=inputs=2:duration=first",
                "-y", output_path
            ]


        subprocess.run(cmd, check=True)
        return output_path

    # def normalize_audio(self, audio_path: str, output_path: str = "", target_level: float = -16.0) -> str:
    #     """
    #     Нормализует громкость аудио
    #
    #     Args:
    #         audio_path: Путь к аудио файлу
    #         output_path: Путь к выходному файлу
    #         target_level: Целевой уровень громкости в dB
    #
    #     Returns:
    #         Путь к нормализованному аудио файлу
    #     """
    #     if not output_path:
    #         output_path = tempfile.mktemp(suffix=".mp3")
    #
    #     # Сначала измеряем текущую громкость
    #     cmd_measure = [
    #         self.config.ffmpeg_path,
    #         "-i", audio_path,
    #         "-af", "loudnorm=print_format=json",
    #         "-f", "null",
    #         "-"
    #     ]

        result = subprocess.run(cmd_measure, capture_output=True, text=True)

        # Извлекаем измеренные значения из вывода
        import json
        import re

        json_match = re.search(r'\{.*\}', result.stderr, re.DOTALL)
        if json_match:
            loudness_stats = json.loads(json_match.group(0))

            # Применяем нормализацию с учетом измеренных значений
            cmd_normalize = [
                self.config.ffmpeg_path,
                "-i", audio_path,
                "-af",
                f"loudnorm=I={target_level}:TP=-1.0:LRA=11:measured_I={loudness_stats.get('input_i', 0)}:measured_TP={loudness_stats.get('input_tp', 0)}:measured_LRA={loudness_stats.get('input_lra', 0)}:measured_thresh={loudness_stats.get('input_thresh', 0)}:offset={loudness_stats.get('target_offset', 0)}:linear=true:print_format=summary",
                "-y", output_path
            ]

            subprocess.run(cmd_normalize, check=True)
            return output_path
        else:
            # Если не удалось получить статистику, применяем простую нормализацию
            cmd_simple = [
                self.config.ffmpeg_path,
                "-i", audio_path,
                "-af", f"loudnorm=I={target_level}:TP=-1.0:LRA=11",
                "-y", output_path
            ]

            subprocess.run(cmd_simple, check=True)
            return output_path

    def extract_audio_from_video(self, video_path: str, output_path: str = "") -> str:
        """
        Извлекает аудио из видео

        Args:
            video_path: Путь к видео файлу
            output_path: Путь к выходному аудио файлу

        Returns:
            Путь к извлеченному аудио файлу
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix=".mp3")

        cmd = [
            self.config.ffmpeg_path,
            "-i", video_path,
            "-vn",  # Отключаем видео
            "-acodec", "libmp3lame",
            "-q:a", "2",
            "-y", output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path

    def replace_audio_in_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        Заменяет аудио в видео

        Args:
            video_path: Путь к видео файлу
            audio_path: Путь к аудио файлу
            output_path: Путь к выходному видео файлу

        Returns:
            Путь к видео с замененным аудио
        """
        cmd = [
            self.config.ffmpeg_path,
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",  # Копируем видео без перекодирования
            "-map", "0:v",  # Берем видео из первого входного файла
            "-map", "1:a",  # Берем аудио из второго входного файла
            "-y", output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path
