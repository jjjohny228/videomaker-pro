import os
import json
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BrandKit:
    def __init__(self,
                 id: str,
                 name: str,
                 intro_settings: Dict[str, Any],
                 clips: List[str],
                 overlay_settings: Dict[str, Any],
                 caption_specs: Dict[str, Any],
                 voice_settings: Dict[str, Any],
                 effects_settings: Dict[str, Any],
                 output_settings: Dict[str, Any]):
        self.id = id
        self.name = name
        self.intro_settings = intro_settings
        self.clips = clips
        self.overlay_settings = overlay_settings
        self.caption_specs = caption_specs
        self.voice_settings = voice_settings
        self.effects_settings = effects_settings
        self.output_settings = output_settings

    @classmethod
    def load(cls, brand_kit_id: str) -> 'BrandKit':
        """
        Загружает настройки брендинга из файла

        Args:
            brand_kit_id: Идентификатор набора брендинга

        Returns:
            Объект BrandKit
        """
        try:
            # Проверяем, существует ли файл с настройками
            config_path = os.path.join("brand_kits", f"{brand_kit_id}.json")
            if not os.path.exists(config_path):
                logger.warning(f"Файл настроек брендинга не найден: {config_path}")
                return cls._create_default(brand_kit_id)

            # Загружаем настройки из файла
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return cls(
                id=brand_kit_id,
                name=data.get("name", f"Brand Kit {brand_kit_id}"),
                intro_settings=data.get("intro_settings", {}),
                clips=data.get("clips", []),
                overlay_settings=data.get("overlay_settings", {}),
                caption_specs=data.get("caption_specs", {}),
                voice_settings=data.get("voice_settings", {}),
                effects_settings=data.get("effects_settings", {}),
                output_settings=data.get("output_settings", {})
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек брендинга: {str(e)}")
            return cls._create_default(brand_kit_id)

    @classmethod
    def _create_default(cls, brand_kit_id: str) -> 'BrandKit':
        """Создает набор настроек брендинга по умолчанию"""
        return cls(
            id=brand_kit_id,
            name=f"Brand Kit {brand_kit_id}",
            intro_settings={
                "duration": 5,
                "font": "Arial",
                "font_size": 48,
                "font_color": "white",
                "background": "black"
            },
            clips=[],
            overlay_settings={
                "watermark": None,
                "avatar": None,
                "cta": None,
                "cta_interval": 120
            },
            caption_specs={
                "font": "Arial",
                "font_size": 24,
                "color": "&HFFFFFF",
                "stroke": 2,
                "stroke_color": "&H000000",
                "position": 2,
                "max_words_per_line": 7
            },
            voice_settings={
                "provider": "edge",
                "voice_id": "",
                "speed": 1.0
            },
            effects_settings={
                "lut": None,
                "mask": None
            },
            output_settings={
                "aspect_ratio": "16:9"
            }
        )

    def save(self) -> bool:
        """
        Сохраняет настройки брендинга в файл

        Returns:
            True, если сохранение успешно, иначе False
        """
        try:
            # Создаем директорию, если она не существует
            os.makedirs("brand_kits", exist_ok=True)

            # Формируем данные для сохранения
            data = {
                "name": self.name,
                "intro_settings": self.intro_settings,
                "clips": self.clips,
                "overlay_settings": self.overlay_settings,
                "caption_specs": self.caption_specs,
                "voice_settings": self.voice_settings,
                "effects_settings": self.effects_settings,
                "output_settings": self.output_settings
            }

            # Сохраняем в файл
            config_path = os.path.join("brand_kits", f"{self.id}.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек брендинга: {str(e)}")
            return False
