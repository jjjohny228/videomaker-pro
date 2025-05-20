import os
import requests
import json
import tempfile
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MinimaxTTS:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.minimax.chat/v1/t2a"

    def generate_audio(self, text: str, voice_id: str = "", speed: float = 1.0, output_file: str = "") -> str:
        """
        Генерирует аудио из текста с помощью Minimax TTS

        Args:
            text: Текст для преобразования в речь
            voice_id: Идентификатор голоса
            speed: Скорость речи (1.0 = нормальная)
            output_file: Путь к выходному файлу

        Returns:
            Путь к сгенерированному аудио файлу
        """
        if not self.api_key:
            raise ValueError("API ключ Minimax не указан")

        if not output_file:
            output_file = tempfile.mktemp(suffix=".mp3")

        # Если voice_id не указан, используем голос по умолчанию
        if not voice_id:
            voice_id = "male-qn-qingse"  # Голос по умолчанию

        # Формируем запрос
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model": "speech-01",
            "voice_id": voice_id,
            "speed": speed
        }

        try:
            # Отправляем запрос
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            # Получаем аудио данные
            audio_data = response.content

            # Сохраняем в файл
            with open(output_file, "wb") as f:
                f.write(audio_data)

            logger.info(f"Аудио успешно сгенерировано: {output_file}")
            return output_file
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса к Minimax API: {str(e)}")
            raise RuntimeError(f"Не удалось сгенерировать аудио: {str(e)}")

    def get_available_voices(self) -> Dict[str, Any]:
        """
        Получает список доступных голосов

        Returns:
            Словарь с информацией о доступных голосах
        """
        # Для Minimax возвращаем предопределенный список голосов
        voices = [
            {"id": "male-qn-qingse", "name": "Мужской голос (Qingse)"},
            {"id": "female-shaonv", "name": "Женский голос (Shaonv)"},
            {"id": "female-zh", "name": "Женский голос (ZH)"},
            {"id": "male-zh", "name": "Мужской голос (ZH)"}
        ]

        return {"voices": voices}
