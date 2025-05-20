import os
import configparser
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()

        # Значения по умолчанию
        self.ffmpeg_path = "ffmpeg"
        self.temp_dir = "temp"
        self.output_dir = "output"
        self.max_workers = 2
        self.randomize_clips = False
        self.minimax_api_key = ""
        self.replicate_api_key = ""
        self.video_codec = "libx264"

        # Загружаем конфигурацию из файла
        self.load()

    def load(self):
        """Загружает конфигурацию из файла"""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path)

                # Загружаем основные настройки
                if "General" in self.config:
                    self.ffmpeg_path = self.config.get("General", "ffmpeg_path", fallback=self.ffmpeg_path)
                    self.temp_dir = self.config.get("General", "temp_dir", fallback=self.temp_dir)
                    self.output_dir = self.config.get("General", "output_dir", fallback=self.output_dir)
                    self.max_workers = self.config.getint("General", "max_workers", fallback=self.max_workers)
                    self.randomize_clips = self.config.getboolean("General", "randomize_clips",
                                                                  fallback=self.randomize_clips)
                    self.video_codec = self.config.get("General", "video_codec", fallback=self.video_codec)

                # Загружаем API ключи
                if "API" in self.config:
                    self.minimax_api_key = self.config.get("API", "minimax_api_key", fallback=self.minimax_api_key)
                    self.replicate_api_key = self.config.get("API", "replicate_api_key",
                                                             fallback=self.replicate_api_key)

                logger.info("Конфигурация успешно загружена")
            else:
                logger.warning(f"Файл конфигурации не найден: {self.config_path}")
                self.save()  # Создаем файл конфигурации со значениями по умолчанию
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {str(e)}")

    def save(self):
        """Сохраняет конфигурацию в файл"""
        try:
            # Создаем секции, если они не существуют
            if "General" not in self.config:
                self.config["General"] = {}
            if "API" not in self.config:
                self.config["API"] = {}

            # Сохраняем основные настройки
            self.config["General"]["ffmpeg_path"] = self.ffmpeg_path
            self.config["General"]["temp_dir"] = self.temp_dir
            self.config["General"]["output_dir"] = self.output_dir
            self.config["General"]["max_workers"] = str(self.max_workers)
            self.config["General"]["randomize_clips"] = str(self.randomize_clips)
            self.config["General"]["video_codec"] = self.video_codec

            # Сохраняем API ключи
            self.config["API"]["minimax_api_key"] = self.minimax_api_key
            self.config["API"]["replicate_api_key"] = self.replicate_api_key

            # Записываем в файл
            with open(self.config_path, "w") as f:
                self.config.write(f)

            logger.info("Конфигурация успешно сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {str(e)}")
