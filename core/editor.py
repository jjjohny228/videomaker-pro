import os
import logging
from typing import Dict, Any, Optional, List
from uuid import uuid4

from core.config import Config
from processors.video_processor import VideoProcessor
from processors.tts_processor import TTSProcessor
from processors.caption_processor import CaptionProcessor
from models.brand_kit import BrandKit
from queue.job_manager import JobManager
from core.config import Config

logger = logging.getLogger(__name__)


class VideoEditor:
    def __init__(self, config_path: str = "config.ini"):
        # self.video_processor = VideoProcessor(self.config)
        # self.tts_processor = TTSProcessor(self.config)
        # self.caption_processor = CaptionProcessor(self.config)
        # self.job_manager = JobManager(max_workers=self.config.max_workers)

        # Создаем временные директории
        os.makedirs(Config.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Config.RESULT_FOLDER, exist_ok=True)

    def create_video(self, title: str, script: str, brand_kit_id: str,
                     callback=None) -> str:
        """
        Создает видео на основе скрипта и настроек брендинга

        Args:
            title: Заголовок видео
            script: Текст скрипта
            brand_kit_id: Идентификатор набора брендинга
            callback: Функция обратного вызова для отслеживания прогресса

        Returns:
            Идентификатор задачи
        """
        job_id = str(uuid4())
        brand_kit = self._load_brand_kit(brand_kit_id)

        # Создаем задачу и добавляем ее в очередь
        self.job_manager.add_job(
            job_id=job_id,
            job_func=self._process_video,
            job_args={
                "title": title,
                "script": script,
                "brand_kit": brand_kit,
                "job_id": job_id
            },
            callback=callback
        )

        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Получает статус задачи по идентификатору"""
        return self.job_manager.get_job_status(job_id)

    def _load_brand_kit(self, brand_kit_id: str) -> BrandKit:
        """Загружает настройки брендинга по идентификатору"""
        # Здесь будет логика загрузки настроек брендинга из хранилища
        # Пока возвращаем тестовые данные
        return BrandKit.load(brand_kit_id)

    def _process_video(self, title: str, script: str, brand_kit: BrandKit,
                       job_id: str, progress_callback=None) -> str:
        """
        Обрабатывает видео согласно скрипту и настройкам брендинга

        Args:
            title: Заголовок видео
            script: Текст скрипта
            brand_kit: Настройки брендинга
            job_id: Идентификатор задачи
            progress_callback: Функция обратного вызова для отслеживания прогресса

        Returns:
            Путь к готовому видео
        """
        job_temp_dir = os.path.join(self.config.temp_dir, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)

        try:
            # Шаг 1: Генерация аудио из скрипта
            self._update_progress(progress_callback, 10, "Генерация аудио из скрипта")
            audio_path = self.tts_processor.generate_audio(
                script,
                brand_kit.voice_settings,
                job_temp_dir
            )

            # Шаг 2: Создание вступительной последовательности
            self._update_progress(progress_callback, 20, "Создание вступления")
            intro_path = self.video_processor.create_intro(
                title,
                brand_kit.intro_settings,
                job_temp_dir
            )

            # Шаг 3: Подготовка основных клипов
            self._update_progress(progress_callback, 30, "Подготовка клипов")
            content_clips = self.video_processor.prepare_content_clips(
                brand_kit.clips,
                audio_path,
                job_temp_dir
            )

            # Шаг 4: Добавление наложений (водяной знак, аватар, призыв к действию)
            self._update_progress(progress_callback, 50, "Добавление наложений")
            overlay_path = self.video_processor.add_overlays(
                content_clips,
                brand_kit.overlay_settings,
                job_temp_dir
            )

            # Шаг 5: Добавление субтитров
            self._update_progress(progress_callback, 70, "Добавление субтитров")
            captioned_path = self.caption_processor.add_captions(
                overlay_path,
                script,
                brand_kit.caption_specs,
                job_temp_dir
            )

            # Шаг 6: Применение эффектов (LUT, маски)
            self._update_progress(progress_callback, 80, "Применение эффектов")
            effects_path = self.video_processor.apply_effects(
                captioned_path,
                brand_kit.effects_settings,
                job_temp_dir
            )

            # Шаг 7: Финализация видео (коррекция соотношения сторон, финальное кодирование)
            self._update_progress(progress_callback, 90, "Финализация видео")
            output_path = self.video_processor.finalize_video(
                effects_path,
                brand_kit.output_settings,
                os.path.join(self.config.output_dir, f"{job_id}.mp4")
            )

            self._update_progress(progress_callback, 100, "Готово")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка обработки видео: {str(e)}")
            raise
        finally:
            # Очистка временных файлов
            # self._cleanup(job_temp_dir)
            pass

    def _update_progress(self, callback, percentage, status):
        """Обновляет прогресс выполнения задачи"""
        if callback:
            callback(percentage, status)
