import os
import random
import subprocess
import time
from typing import List, Dict, Any, Optional
import logging

from core.config import Config
from utils.ffmpeg_utils import FFmpegUtils
from database.models import BrandKit

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, brand_kit: BrandKit):
        self.brand_kit = brand_kit
        self.ffmpeg = FFmpegUtils()
        self.temp_dir = Config.TEMP_FOLDER

    def join_clips_with_transitions(self) -> str:
        """
        Подготавливает основные клипы контента с переходами

        Args:
            clips: Список путей к клипам
            transitions: Список типов переходов
            temp_dir: Временная директория

        Returns:
            Путь к подготовленному видео
        """
        source_videos = self.brand_kit.source_videos_paths
        transitions = self.brand_kit.transition_names
        if not source_videos:
            raise ValueError("clips list is empty")
        if not transitions:
            raise ValueError("transitions list is empty")

        # Рандомно перемешиваем переходы
        random.shuffle(transitions)

        output_file = f'{self.temp_dir}/{int(time.time())}_content_with_transitions.mp4'
        temp_files = []
        normalized_clips = []

        try:
            # Определяем целевое разрешение
            width, height = self._get_resolution_from_aspect_ratio()
            target_resolution = f'{width}:{height}'

            # Нормализуем все клипы к одному размеру
            for i, clip in enumerate(source_videos):
                normalized_clip = os.path.join(self.temp_dir, f"normalized_{i}.mp4")

                # Используем новую функцию из ffmpeg_utils
                self.ffmpeg.normalize_video_resolution(clip, normalized_clip, target_resolution)

                normalized_clips.append(normalized_clip)
                temp_files.append(normalized_clip)

            # Если только один клип, возвращаем нормализованный
            if len(normalized_clips) == 1:
                return self.ffmpeg.copy_file(normalized_clips[0], output_file)

            # Применяем переходы между нормализованными клипами
            current_video = normalized_clips[0]

            for i in range(1, len(normalized_clips)):
                transition_type = transitions[(i - 1) % len(transitions)]
                next_clip = normalized_clips[i]

                temp_output = os.path.join(self.temp_dir, f"transition_result_{i}.mp4")
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
            final_result = self.ffmpeg.copy_file(current_video, output_file)
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

    def add_overlays(self, video_path: str) -> str:
        """
        Добавляет наложения на видео (водяной знак, аватар, призыв к действию)

        """
        output_file = f'{self.temp_dir}/{int(time.time())}_overlayed.mp4'

        # Получаем информацию о видео
        background_width, background_height  = self.ffmpeg.get_video_info(video_path)
        duration = self.ffmpeg.get_video_duration(video_path)

        positions = {
            "top_right": "W-w-W/20:H/20",
            "top_left": "W/20:H/20",
            "top_center": "(W-w)/2:H/20",
            "bottom_right": "W-w-W/20:H-h-H/20",
            "bottom_left": "W/20:H-h-H/20",
            "bottom_center": "(W-w)/2:H-h-H/20",
            "center": "(W-w)/2:(H-h)/2"
        }

        filter_complex = []
        inputs = ["-i", video_path]
        input_index = 1
        current_video = "[0:v]"

        # Добавляем водяной знак
        if self.brand_kit.watermark_path:
            watermark = self.brand_kit.watermark_path
            inputs.extend(["-i", watermark])

            # Масштабируем водяной знак если нужно
            watermark_width_part = self.brand_kit.watermark_width_persent / 100
            watermark_position_input = self.brand_kit.watermark_position

            watermark_position = positions.get(watermark_position_input)

            filter_complex.append(f"[{input_index}:v]scale={background_width}*{watermark_width_part}:-1[wm]")
            filter_complex.append(f"{current_video}[wm]overlay={watermark_position}[v{input_index}]")
            current_video = f"[v{input_index}]"
            input_index += 1

        # Добавляем аватар
        if self.brand_kit.avatar_path:
            avatar = self.brand_kit.avatar_path
            avatar_position_input = self.brand_kit.avatar_position
            avatar_width_part_of_video_width = self.brand_kit.avatar_width_persent / 100
            background_color = self.brand_kit.avatar_background_color
            similarity = 0.3
            blend = 0.1

            # Определяем позицию аватара
            avatar_position = positions.get(avatar_position_input)

            inputs.extend(["-i", avatar])

            avatar_filter = f"[{input_index}:v]"

            # Удаляем задний фон
            avatar_filter += f"colorkey={background_color}:similarity={similarity}:blend={blend},"

            # Зацикливаем аватар на всю длительность видео
            avatar_filter += f"loop=loop=-1:size=32767:start=0,setpts=PTS-STARTPTS,trim=duration={duration},"

            # Масштабируем (БЕЗ промежуточной метки)
            avatar_filter += f"scale={background_width}*{avatar_width_part_of_video_width}:-1[avatar_scaled]"

            filter_complex.append(avatar_filter)
            filter_complex.append(f"{current_video}[avatar_scaled]overlay={avatar_position}[v{input_index}]")
            current_video = f"[v{input_index}]"
            input_index += 1

        # Добавляем призыв к действию
        if self.brand_kit.cta_path:
            cta = self.brand_kit.cta_path
            cta_interval = self.brand_kit.cta_interval
            cta_duration = self.brand_kit.cta_duration
            cta_size_width_part_of_background = self.brand_kit.cta_width_persent / 100
            cta_position = self.brand_kit.cta_position

            cta_ffmpeg_position = positions.get(cta_position)

            inputs.extend(["-i", cta])

            # Обрабатываем CTA
            cta_filter = f"[{input_index}:v]scale={background_width};{cta_size_width_part_of_background}:-1[cta]"
            filter_complex.append(cta_filter)

            # Показываем CTA с интервалами
            overlay_filter = f"{current_video}[cta]overlay={cta_ffmpeg_position}:enable='gt(mod(t,{cta_interval}),{cta_interval - cta_duration})'[v{input_index}]"
            filter_complex.append(overlay_filter)
            current_video = f"[v{input_index}]"
            input_index += 1

        # Если нет наложений, просто копируем видео
        if not filter_complex:
            return self.ffmpeg.copy_file(video_path, output_file)

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

    def apply_effects(self, video_path: str) -> str:
        """
        Применяет эффекты к видео (LUT, маски)

        Args:
            video_path: Путь к видео
            effects_settings: Настройки эффектов
            temp_dir: Временная директория

        Returns:
            Путь к видео с эффектами
        """
        output_file = f'{self.temp_dir}/{int(time.time())}_effects.mp4'
        current_video = video_path
        temp_files = []

        # Применяем LUT
        if self.brand_kit.lut_path:
            lut_file = self.brand_kit.lut_path
            lut_output = os.path.join(self.temp_dir, f"{int(time.time())}_lut_effect.mp4")
            cmd = [
                'ffmpeg',
                "-i", current_video,
                "-vf", f"lut3d={lut_file}",
                "-c:v", Config.VIDEO_CODEC,
                "-c:a", "copy",
                "-y", lut_output
            ]
            subprocess.run(cmd, check=True)
            temp_files.append(lut_output)
            current_video = lut_output

        # В функции apply_effects замените логику масштабирования:
        if self.brand_kit.mask_effect_path:
            mask_file = self.brand_kit.mask_effect_path
            mask_bg_color = self.brand_kit.mask_effect_background_color
            similarity = 0.3
            blend = 0.1

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

            mask_output = os.path.join(self.temp_dir,f"{int(time.time())}_masked.mp4")

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
            temp_files.append(mask_output)
            current_video = mask_output

        # Если никаких эффектов не применялось, копируем исходное видео
        if current_video == video_path:
            return self.ffmpeg.copy_file(video_path, output_file)

        result_file = self.ffmpeg.copy_file(current_video, output_file)
        for file in temp_files:
            os.remove(file)
        return result_file

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
            return self.ffmpeg.copy_file(video_path, output_file)

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
