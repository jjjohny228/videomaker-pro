import os
import random
import subprocess
from typing import List, Dict, Any, Optional
import logging

from core.config import Config
from utils.ffmpeg_utils import FFmpegUtils
# from database.brand_kit import BrandKit

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, config):
        self.config = config
        self.ffmpeg = FFmpegUtils()

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
            "ffmpeg",
            "-f", "lavfi", "-i", f"color=c={background}:s=1920x1080:d={duration}",
            "-vf", f"subtitles={subtitle_file}",
            "-c:v", Config.VIDEO_CODEC, "-preset", "medium", "-crf", "22",
            "-y", output_file
        ]

        subprocess.run(cmd, check=True)
        return output_file

    def prepare_content_clips(self, clips: List[str], transitions: List[str], temp_dir: str) -> str:
        """
        Подготавливает основные клипы контента с переходами

        Args:
            clips: Список путей к клипам
            transitions: Список типов переходов
            temp_dir: Временная директория

        Returns:
            Путь к подготовленному видео
        """
        if not clips:
            raise ValueError("clips list is empty")
        if not transitions:
            raise ValueError("transitions list is empty")

        # Рандомно перемешиваем переходы
        import random
        random.shuffle(transitions)

        output_file = os.path.join(temp_dir, "content_with_transitions.mp4")
        temp_files = []
        normalized_clips = []

        try:
            # Определяем целевое разрешение
            target_resolution = self.config.get('target_resolution', '1080x1920')

            # Нормализуем все клипы к одному размеру
            for i, clip in enumerate(clips):
                normalized_clip = os.path.join(temp_dir, f"normalized_{i}.mp4")

                # Используем новую функцию из ffmpeg_utils
                self.ffmpeg.normalize_video_resolution(clip, normalized_clip, target_resolution)

                normalized_clips.append(normalized_clip)
                temp_files.append(normalized_clip)

            # Если только один клип, возвращаем нормализованный
            if len(normalized_clips) == 1:
                return self._copy_file(normalized_clips[0], output_file)

            # Применяем переходы между нормализованными клипами
            current_video = normalized_clips[0]

            for i in range(1, len(normalized_clips)):
                transition_type = transitions[(i - 1) % len(transitions)]
                next_clip = normalized_clips[i]

                temp_output = os.path.join(temp_dir, f"transition_result_{i}.mp4")
                temp_files.append(temp_output)

                # Создаем переход между клипами
                self.ffmpeg.create_transition(
                    clip1=current_video,
                    clip2=next_clip,
                    output=temp_output,
                    transition_type=transition_type,
                    duration=0.5
                )

                current_video = temp_output

            # Копируем финальный результат
            final_result = self._copy_file(current_video, output_file)
            logger.info(f"Successfully created content with transitions: {output_file}")

            return final_result

        except Exception as e:
            logger.error(f"Error preparing content clips: {str(e)}")
            raise
        finally:
            # Удаляем временные файлы
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error deleting temporary file {file_path}: {e}")

    def add_overlays(self, video_path: str, overlay_settings: Dict[str, Any], temp_dir: str) -> str:
        """
        Добавляет наложения на видео (водяной знак, аватар, призыв к действию)

        """
        output_file = os.path.join(temp_dir, "overlays.mp4")

        # Получаем информацию о видео
        background_width, background_height  = self.ffmpeg.get_video_info(video_path)
        duration = self.ffmpeg.get_video_duration(video_path)

        positions = {
            "top-right": "W-w-W/20:H/20",
            "top-left": "W/20:H/20",
            "bottom-right": "W-w-W/20:H-h-H/20",
            "bottom-left": "W/20:H-h-H/20",
            "center": "(W-w)/2:(H-h)/2"
        }

        filter_complex = []
        inputs = ["-i", video_path]
        input_index = 1
        current_video = "[0:v]"

        # Добавляем водяной знак
        if overlay_settings.get("watermark"):
            watermark = overlay_settings["watermark"]
            inputs.extend(["-i", watermark])

            # Масштабируем водяной знак если нужно
            watermark_width_part = overlay_settings.get("watermark_width")
            watermark_position_input = overlay_settings.get("watermark_position")

            watermark_position = positions.get(watermark_position_input)

            filter_complex.append(f"[{input_index}:v]scale={background_width}/{watermark_width_part}:-1[wm]")
            filter_complex.append(f"{current_video}[wm]overlay={watermark_position}[v{input_index}]")
            current_video = f"[v{input_index}]"
            input_index += 1

        # Добавляем аватар
        if overlay_settings.get("avatar"):
            avatar = overlay_settings["avatar"]
            avatar_position_input = overlay_settings.get("avatar_position", "bottom-right")
            avatar_width_part_of_video_width = overlay_settings.get("avatar_width")
            background_color = overlay_settings.get("avatar_bg_color")
            similarity = overlay_settings.get("bg_similarity", "0.3")
            blend = overlay_settings.get("bg_blend", "0.1")

            # Определяем позицию аватара
            avatar_position = positions.get(avatar_position_input)

            inputs.extend(["-i", avatar])

            avatar_filter = f"[{input_index}:v]"

            # Удаляем задний фон
            avatar_filter += f"colorkey={background_color}:similarity={similarity}:blend={blend},"

            # Зацикливаем аватар на всю длительность видео
            avatar_filter += f"loop=loop=-1:size=32767:start=0,setpts=PTS-STARTPTS,trim=duration={duration},"

            # Масштабируем (БЕЗ промежуточной метки)
            avatar_filter += f"scale={background_width}/{avatar_width_part_of_video_width}:-1[avatar_scaled]"

            filter_complex.append(avatar_filter)
            filter_complex.append(f"{current_video}[avatar_scaled]overlay={avatar_position}[v{input_index}]")
            current_video = f"[v{input_index}]"
            input_index += 1

        # Добавляем призыв к действию
        if overlay_settings.get("cta"):
            cta = overlay_settings["cta"]
            cta_interval = overlay_settings.get("cta_interval", 6)
            cta_duration = overlay_settings.get("cta_duration", 2)
            cta_size_width_part_of_background = overlay_settings.get("cta_width")
            cta_position = overlay_settings.get("cta_position", "top-right")

            cta_pos = positions.get(cta_position, "W-w-10:10")

            inputs.extend(["-i", cta])

            # Обрабатываем CTA
            cta_filter = f"[{input_index}:v]scale={background_width}/{cta_size_width_part_of_background}:-1[cta]"
            filter_complex.append(cta_filter)

            # Показываем CTA с интервалами
            overlay_filter = f"{current_video}[cta]overlay={cta_pos}:enable='gt(mod(t,{cta_interval}),{cta_interval - cta_duration})'[v{input_index}]"
            filter_complex.append(overlay_filter)
            current_video = f"[v{input_index}]"
            input_index += 1

        # Если нет наложений, просто копируем видео
        if not filter_complex:
            return self._copy_file(video_path, output_file)

        # Собираем команду FFmpeg
        cmd = [
            'ffmpeg',
            *inputs,
            "-filter_complex", ";".join(filter_complex),
            "-map", current_video, "-map", "0:a?",
            "-c:v", Config.VIDEO_CODEC,
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
        current_video = video_path

        # Применяем LUT
        if effects_settings.get("lut"):
            lut_file = effects_settings.get("lut")
            lut_output = os.path.join(temp_dir, "lut_effect.mp4")
            cmd = [
                'ffmpeg',
                "-i", current_video,
                "-vf", f"lut3d={lut_file}",
                "-c:v", Config.VIDEO_CODEC,
                "-c:a", "copy",
                "-y", lut_output
            ]
            subprocess.run(cmd, check=True)
            current_video = lut_output

        # В функции apply_effects замените логику масштабирования:
        if effects_settings.get("mask"):
            mask_file = effects_settings["mask"]
            mask_bg_color = effects_settings.get("mask_bg_color", "00ff00")
            similarity = effects_settings.get("mask_similarity", "0.3")
            blend = effects_settings.get("mask_blend", "0.1")

            # Получаем информацию о видео и маске
            video_width, video_height = self.ffmpeg.get_video_info(current_video)
            video_duration = self.ffmpeg.get_video_duration(current_video)
            mask_width, mask_height = self.ffmpeg.get_video_info(mask_file)

            # Определяем наибольшую сторону видео
            max_video_dimension = max(video_width, video_height)

            # Определяем как масштабировать маску в зависимости от её ориентации
            if video_width > video_height:
                # Маска горизонтальная - масштабируем по ширине
                scale_filter = f"scale={video_width}:-1"
            else:
                # Маска вертикальная - масштабируем по высоте
                scale_filter = f"scale=-1:{video_height}"

            overlay_position = "(main_w-overlay_w)/2:(main_h-overlay_h)/2"

            mask_output = os.path.join(temp_dir, "mask_effect.mp4")

            filter_complex = (
                f"[1:v]loop=loop=-1:size=32767:start=0,setpts=PTS-STARTPTS,trim=duration={video_duration},"
                f"colorkey={mask_bg_color}:similarity={similarity}:blend={blend},"
                f"{scale_filter}[mask_processed];"
                f"[0:v][mask_processed]overlay={overlay_position}[out]"
            )

            cmd = [
                'ffmpeg',
                "-i", current_video,
                "-i", mask_file,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "0:a?",
                "-c:v", Config.VIDEO_CODEC,
                "-c:a", "copy",
                "-y", mask_output
            ]
            subprocess.run(cmd, check=True)
            current_video = mask_output

        # Если никаких эффектов не применялось, копируем исходное видео
        if current_video == video_path:
            return self._copy_file(video_path, output_file)

        # Если применялись эффекты, но финальный файл не effects.mp4, переименовываем
        if current_video != output_file:
            return self._copy_file(current_video, output_file)

        return current_video

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
        aspect_ratio = output_settings.get("aspect_ratio")

        video_width, video_height = self.ffmpeg.get_video_info(video_path)

        if aspect_ratio == "16:9":
            width, height = 1920, 1080
        elif aspect_ratio == "9:16":
            width, height = 1080, 1920
        else:
            width, height = 1920, 1080

        if video_width == width and video_height == height:
            return self._copy_file(video_path, output_file)

        # Финализируем видео
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", Config.VIDEO_CODEC,
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

    def _create_typewriter_into_title(self, text: str, output_file: str, font: str, font_size: int, font_color: str):
        """Создает ASS-файл с эффектом печатной машинки (правильная версия)"""

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Убираем переносы строк и лишние пробелы
        text = text.replace('\n', ' ').replace('\r', ' ').strip()

        ass_content = f"""[Script Info]
    Title: Typewriter Effect
    ScriptType: v4.00+
    PlayResX: 1920
    PlayResY: 1080

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
