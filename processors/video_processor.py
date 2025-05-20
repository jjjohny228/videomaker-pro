import os
import subprocess
from typing import List, Dict, Any, Optional
import logging

from utils.ffmpeg_utils import FFmpegUtils
from models.brand_kit import BrandKit

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, config):
        self.config = config
        self.ffmpeg = FFmpegUtils(config.ffmpeg_path)

    def create_intro(self, title: str, intro_settings: Dict[str, Any], temp_dir: str) -> str:
        """
        Создает вступительную последовательность с эффектом печатной машинки

        Args:
            title: Заголовок видео
            intro_settings: Настройки вступления
            temp_dir: Временная директория

        Returns:
            Путь к созданному вступлению
        """
        output_file = os.path.join(temp_dir, "intro.mp4")

        # Если есть готовый интро-клип
        if intro_settings.get("intro_clip"):
            # Копируем интро-клип во временную директорию
            intro_clip = intro_settings["intro_clip"]
            return self._copy_file(intro_clip, output_file)

        # Создаем интро с эффектом печатной машинки
        background = intro_settings.get("background", "black")
        font = intro_settings.get("font", "Arial")
        font_size = intro_settings.get("font_size", 48)
        font_color = intro_settings.get("font_color", "white")
        duration = intro_settings.get("duration", 5)

        # Создаем ASS-файл с эффектом печатной машинки
        subtitle_file = os.path.join(temp_dir, "intro_text.ass")
        self._create_typewriter_subtitle(title, subtitle_file, font, font_size, font_color)

        # Создаем видео с субтитрами
        cmd = [
            self.config.ffmpeg_path,
            "-f", "lavfi", "-i", f"color=c={background}:s=1920x1080:d={duration}",
            "-vf", f"subtitles={subtitle_file}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-y", output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def prepare_content_clips(self, clips: List[str], audio_path: str, temp_dir: str) -> str:
        """
        Подготавливает основные клипы контента

        Args:
            clips: Список путей к клипам
            audio_path: Путь к аудио файлу
            temp_dir: Временная директория

        Returns:
            Путь к подготовленному видео
        """
        output_file = os.path.join(temp_dir, "content.mp4")

        # Получаем длительность аудио
        audio_duration = self.ffmpeg.get_duration(audio_path)

        # Если клипы нужно воспроизводить в случайном порядке
        if self.config.randomize_clips:
            import random
            random.shuffle(clips)

        # Создаем файл со списком клипов для конкатенации
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")

        # Объединяем клипы
        cmd = [
            self.config.ffmpeg_path,
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-strict", "experimental",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-y", output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def add_overlays(self, video_path: str, overlay_settings: Dict[str, Any], temp_dir: str) -> str:
        """
        Добавляет наложения на видео (водяной знак, аватар, призыв к действию)

        Args:
            video_path: Путь к видео
            overlay_settings: Настройки наложений
            temp_dir: Временная директория

        Returns:
            Путь к видео с наложениями
        """
        output_file = os.path.join(temp_dir, "overlays.mp4")

        # Получаем информацию о видео
        video_info = self.ffmpeg.get_video_info(video_path)
        width, height = video_info["width"], video_info["height"]

        filter_complex = []
        inputs = ["-i", video_path]
        maps = []

        # Добавляем водяной знак
        if overlay_settings.get("watermark"):
            watermark = overlay_settings["watermark"]
            inputs.extend(["-i", watermark])
            filter_complex.append(f"[0:v][1:v]overlay=W-w-10:H-h-10[v1]")
            maps.append("[v1]")

        # Добавляем аватар
        if overlay_settings.get("avatar"):
            avatar = overlay_settings["avatar"]
            avatar_position = overlay_settings.get("avatar_position", "bottom-right")

            # Определяем позицию аватара
            if avatar_position == "bottom-right":
                position = "W-w-10:H-h-10"
            elif avatar_position == "bottom-left":
                position = "10:H-h-10"
            elif avatar_position == "top-right":
                position = "W-w-10:10"
            elif avatar_position == "top-left":
                position = "10:10"
            else:
                position = "W-w-10:H-h-10"

            inputs.extend(["-i", avatar])
            if maps:
                filter_complex.append(f"[{maps[-1][1:-1]}][2:v]overlay={position}[v2]")
                maps.append("[v2]")
            else:
                filter_complex.append(f"[0:v][1:v]overlay={position}[v2]")
                maps.append("[v2]")

        # Добавляем призыв к действию
        if overlay_settings.get("cta"):
            cta = overlay_settings["cta"]
            cta_interval = overlay_settings.get("cta_interval", 120)

            inputs.extend(["-i", cta])
            if maps:
                filter_complex.append(
                    f"[{maps[-1][1:-1]}][{len(inputs) // 2}:v]overlay=W-w-10:10:enable='gt(mod(t,{cta_interval}),{cta_interval - 5})'[v3]"
                )
                maps.append("[v3]")
            else:
                filter_complex.append(
                    f"[0:v][1:v]overlay=W-w-10:10:enable='gt(mod(t,{cta_interval}),{cta_interval - 5})'[v3]"
                )
                maps.append("[v3]")

        # Если нет наложений, просто копируем видео
        if not filter_complex:
            return self._copy_file(video_path, output_file)

        # Собираем команду FFmpeg
        cmd = [
            self.config.ffmpeg_path,
            *inputs,
            "-filter_complex", ";".join(filter_complex),
            "-map", maps[-1], "-map", "0:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-c:a", "copy",
            "-y", output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def apply_effects(self, video_path: str, effects_settings: Dict[str, Any], temp_dir: str) -> str:
        """
        Применяет эффекты к видео (LUT, маски)

        Args:
            video_path: Путь к видео
            effects_settings: Настройки эффектов
            temp_dir: Временная директория

        Returns:
            Путь к видео с эффектами
        """
        output_file = os.path.join(temp_dir, "effects.mp4")

        # Применяем LUT
        if effects_settings.get("lut"):
            lut_file = effects_settings["lut"]
            cmd = [
                self.config.ffmpeg_path,
                "-i", video_path,
                "-vf", f"lut3d={lut_file}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "copy",
                "-y", output_file
            ]
            subprocess.run(cmd, check=True)
            video_path = output_file

        # Применяем маску
        if effects_settings.get("mask"):
            mask_file = effects_settings["mask"]
            output_file_mask = os.path.join(temp_dir, "mask_effect.mp4")
            cmd = [
                self.config.ffmpeg_path,
                "-i", video_path,
                "-i", mask_file,
                "-filter_complex", "[0:v][1:v]overlay=0:0",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "copy",
                "-y", output_file_mask
            ]
            subprocess.run(cmd, check=True)
            return output_file_mask

        # Если нет эффектов, просто копируем видео
        if not effects_settings.get("lut"):
            return self._copy_file(video_path, output_file)

        return output_file

    def finalize_video(self, video_path: str, output_settings: Dict[str, Any], output_file: str) -> str:
        """
        Финализирует видео (коррекция соотношения сторон, финальное кодирование)

        Args:
            video_path: Путь к видео
            output_settings: Настройки вывода
            output_file: Путь к выходному файлу

        Returns:
            Путь к финальному видео
        """
        # Определяем соотношение сторон
        aspect_ratio = output_settings.get("aspect_ratio", "16:9")

        if aspect_ratio == "16:9":
            width, height = 1920, 1080
        elif aspect_ratio == "9:16":
            width, height = 1080, 1920
        else:
            width, height = 1920, 1080

        # Финализируем видео
        cmd = [
            self.config.ffmpeg_path,
            "-i", video_path,
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-y", output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def _copy_file(self, src: str, dst: str) -> str:
        """Копирует файл из src в dst"""
        import shutil
        shutil.copy2(src, dst)
        return dst

    def _create_typewriter_subtitle(self, text: str, output_file: str, font: str, font_size: int, font_color: str):
        """Создает ASS-файл с эффектом печатной машинки"""
        # Реализация создания ASS-файла с эффектом печатной машинки
        # Здесь будет использоваться логика из примера кода
        pass
