import os
from typing import Dict, Any, Optional
import logging

from services.edge_tts import EdgeTTS
from services.minimax_tts import MinimaxTTS
from services.replicate_tts import ReplicateTTS

logger = logging.getLogger(__name__)


class TTSProcessor:
    def __init__(self, config):
        self.config = config
        self.providers = {
            "edge": EdgeTTS(),
            "minimax": MinimaxTTS(config.minimax_api_key),
            "replicate": ReplicateTTS(config.replicate_api_key)
        }

    def generate_audio(self, text: str, voice_settings: Dict[str, Any], output_dir: str) -> str:
        """
        Генерирует аудио из текста

        Args:
            text: Текст для преобразования в речь
            voice_settings: Настройки голоса
            output_dir: Директория для сохранения аудио

        Returns:
            Путь к сгенерированному аудио файлу
        """
        provider_name = voice_settings.get("provider", "edge")
        voice_id = voice_settings.get("voice_id", "")
        speed = voice_settings.get("speed", 1.0)

        if provider_name not in self.providers:
            raise ValueError(f"Неизвестный провайдер TTS: {provider_name}")

        provider = self.providers[provider_name]
        output_file = os.path.join(output_dir, "speech.mp3")

        try:
            return provider.generate_audio(text, voice_id, speed, output_file)
        except Exception as e:
            logger.error(f"Ошибка генерации аудио: {str(e)}")
            # Если основной провайдер не сработал, пробуем запасной вариант
            fallback_provider = self.providers["edge"]
            return fallback_provider.generate_audio(text, "", speed, output_file)
