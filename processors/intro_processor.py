import logging
import time

from database.models import BrandKit
from utils.ffmpeg_utils import FFmpegUtils
from core.config import Config
import os
import time
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class IntroProcessor:
    def __init__(self, brand_kit: BrandKit):
        self.brand_kit = brand_kit
        self.ffmpeg = FFmpegUtils()
        self.temp_dir = Config.TEMP_FOLDER

    def create_intro(self) -> str:
        """
        Creates an intro sequence with typewriter effect
        Supports different background types: color, image, video
        """
        output_file = f'{self.temp_dir}/{int(time.time())}_intro.mp4'

        # If there's a ready intro clip
        intro_clip = self.brand_kit.intro_clip_path
        if intro_clip:
            if not os.path.exists(intro_clip):
                raise FileNotFoundError(f'Intro clip file: {intro_clip} does not exist')
            return self.ffmpeg.copy_file(intro_clip, output_file)

        intro_config = self.brand_kit.auto_intro_settings
        if not intro_config:
            raise ValueError("Auto intro settings not configured for this brand kit")

        # Get parameters
        background_type = intro_config.background_type
        background_value = intro_config.background_value
        text = intro_config.text
        font = intro_config.title_font
        font_size = intro_config.title_font_size
        font_color = intro_config.title_font_color
        duration = intro_config.duration

        # Determine resolution based on aspect_ratio
        resolution = self._get_resolution_from_aspect_ratio()

        # Validate and process background
        background_input = self._prepare_background(background_type, background_value, duration, resolution)

        # Create ASS file with typewriter effect
        title_ass_file = self._create_typewriter_into_title(text, font, font_size, font_color)

        # Create video with subtitles
        cmd = [
            "ffmpeg",
            "-f", "lavfi" if background_type == "color" else "concat",
            "-i", background_input,
            "-vf", f"subtitles={title_ass_file}",
            "-c:v", Config.VIDEO_CODEC,
            "-t", str(duration),  # Limit duration
            "-y", output_file
        ]

        # If background is not color, change command structure
        if background_type != "color":
            cmd = [
                "ffmpeg",
                "-i", background_input,
                "-vf", f"subtitles={title_ass_file}",
                "-c:v", Config.VIDEO_CODEC,
                "-preset", "medium",
                "-crf", "22",
                "-t", str(duration),
                "-y", output_file
            ]

        try:
            self.ffmpeg.run_command(cmd)
            return output_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error creating intro video: {e.stderr}")

    def _get_resolution_from_aspect_ratio(self) -> tuple:
        """
        Returns resolution based on aspect_ratio

        """
        aspect_ratio = self.brand_kit.aspect_ratio

        if aspect_ratio == "16:9":
            return 1920, 1080
        elif aspect_ratio == "9:16":
            return 1080, 1920
        else:
            # Default to 16:9
            return 1920, 1080

    def _prepare_background(self, background_type: str, background_value: str, duration: int, resolution: tuple) -> str:
        """
        Prepares background for intro based on type

        """
        width, height = resolution

        if background_type == "color":
            return self._prepare_color_background(background_value, width, height, duration)
        elif background_type == "image":
            return self._prepare_image_background(background_value, width, height, duration)
        elif background_type == "video":
            return self._prepare_video_background(background_value, width, height, duration)
        else:
            raise ValueError(f"Unsupported background type: {background_type}")

    def _prepare_color_background(self, color_value: str, width: int, height: int, duration: int) -> str:
        """Prepares color background"""
        # Validate and format color
        formatted_color = self._validate_color(color_value)
        return f"color=c={formatted_color}:s={width}x{height}:d={duration}"

    def _prepare_image_background(self, image_path: str, width: int, height: int, duration: int) -> str:
        """Prepares background from image"""
        if not image_path:
            raise ValueError("Image path is required for image background type")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Background image not found: {image_path}")

        # Check file extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid image format. Supported: {', '.join(valid_extensions)}")

        # Create temporary video file from image
        temp_video = f'{self.temp_dir}/{int(time.time())}_bg_image.mp4'

        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", image_path,
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", Config.VIDEO_CODEC,
            "-t", str(duration),
            "-y", temp_video
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return temp_video
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error processing background image: {e.stderr}")

    def _prepare_video_background(self, video_path: str, width: int, height: int, duration: int) -> str:
        """Prepares background from video"""
        if not video_path:
            raise ValueError("Video path is required for video background type")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Background video not found: {video_path}")

        # Check file extension
        valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        if not any(video_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid video format. Supported: {', '.join(valid_extensions)}")

        # Normalize video and trim by duration
        temp_normalized = f'{self.temp_dir}/{int(time.time())}_bg_normalized.mp4'

        # First normalize resolution
        normalized_video = self.ffmpeg.normalize_video_resolution(
            video_path,
            temp_normalized,
            f"{width}:{height}"
        )

        # Then trim by duration and loop if needed
        temp_final = f'{self.temp_dir}/{int(time.time())}_bg_final.mp4'

        cmd = [
            "ffmpeg",
            "-stream_loop", "-1",  # Loop video
            "-i", normalized_video,
            "-t", str(duration),  # Trim to needed duration
            "-c:v", Config.VIDEO_CODEC,
            "-c:a", "copy",
            "-y", temp_final
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return temp_final
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error processing background video: {e.stderr}")

    @staticmethod
    def _validate_color(color_value: str) -> str:
        """
        Validates and formats color for FFmpeg
        Accepts only hex colors in RRGGBB format
        """
        if not color_value:
            return "0x000000"

        color = str(color_value).strip()

        # Remove # if present
        if color.startswith('#'):
            color = color[1:]

        # Check if it's a valid hex color (6 characters)
        if len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color):
            return f"0x{color.upper()}"

        # Check short format (3 characters) and expand to 6
        if len(color) == 3 and all(c in '0123456789abcdefABCDEF' for c in color):
            expanded = ''.join([c * 2 for c in color])
            return f"0x{expanded.upper()}"

        # Reject invalid input
        raise ValueError(f"Invalid hex color format: '{color_value}'. Expected format: RRGGBB or #RRGGBB")

    def _create_typewriter_into_title(self, text: str, font: str, font_size: int, font_color: str):
        """Создает ASS-файл с эффектом печатной машинки (правильная версия)"""

        output_file = f'{self.temp_dir}/{int(time.time())}_title_ass.ass'

        # Убираем переносы строк и лишние пробелы
        text = text.replace('\n', ' ').replace('\r', ' ').strip()
        width, height = self._get_resolution_from_aspect_ratio()

        ass_content = f"""[Script Info]
    Title: Typewriter Effect
    ScriptType: v4.00+
    PlayResX: {width}
    PlayResY: {height}

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    Style: Default,{font},{font_size},{self._color_to_ass(font_color)},&HFF000000,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,200,200,100,1

    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    """

        # Рассчитываем время для каждой буквы
        total_duration = 3.0
        char_count = len(text)
        char_duration_cs = int((total_duration * 100) / char_count) if char_count > 0 else 10

        # Создаем ОДИН диалог с karaoke тегами
        karaoke_text = ""
        for char in text:
            if char == ' ':
                karaoke_text += f"{{\\k{char_duration_cs}}} "
            else:
                karaoke_text += f"{{\\k{char_duration_cs}}}{char}"

        # Один диалог для всего текста
        end_time = self._seconds_to_ass_time(5.0)
        ass_content += f"Dialogue: 0,0:00:00.00,{end_time},Default,,0,0,0,,{karaoke_text}\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        return output_file

    def _color_to_ass(self, color: str) -> str:
        """Конвертирует цвет в формат ASS"""
        color_map = {
            'white': '&H00FFFFFF',
            'black': '&H00000000',
            'red': '&H000000FF',
            'green': '&H0000FF00',
            'blue': '&H00FF0000',
            'yellow': '&H0000FFFF',
            'cyan': '&H00FFFF00',
            'magenta': '&H00FF00FF'
        }

        if color.lower() in color_map:
            return color_map[color.lower()]

        # Если цвет в формате hex (#RRGGBB)
        if color.startswith('#') and len(color) == 7:
            # Конвертируем из #RRGGBB в &H00BBGGRR (ASS использует BGR)
            r = color[1:3]
            g = color[3:5]
            b = color[5:7]
            return f"&H00{b.upper()}{g.upper()}{r.upper()}"

        return '&H00FFFFFF'  # По умолчанию белый

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Конвертирует секунды в формат времени ASS (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


