# Chat gpt

import requests
import tempfile
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ReplicateTTS:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.replicate.com/v1/predictions"

    def generate_audio(self, text: str, voice_id: str = "", speed: float = 1.0, output_file: str = "") -> str:
        """
        Генерирует аудио из текста с помощью Replicate TTS

        Args:
            text: Текст для преобразования в речь
            voice_id: Идентификатор голоса (или модели)
            speed: Скорость речи (1.0 = нормальная)
            output_file: Путь к выходному файлу

        Returns:
            Путь к сгенерированному аудио файлу
        """
        if not self.api_key:
            raise ValueError("API ключ Replicate не указан")

        if not output_file:
            output_file = tempfile.mktemp(suffix=".mp3")

        # Если voice_id не указан, используем модель по умолчанию
        if not voice_id:
            voice_id = "suno-ai/bark"  # Модель по умолчанию

        # Формируем запрос
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

        # Параметры зависят от выбранной модели
        if voice_id == "suno-ai/bark":
            data = {
                "version": "b76242b40d67c76ab6742e987628478ed2fb5b20014e0e19e83f53c2d7f3fd2e",
                "input": {
                    "text": text,
                    "history_prompt": "v2/ru_speaker_1",  # Русский голос
                    "text_temp": 0.7,
                    "waveform_temp": 0.7,
                    "speed": speed
                }
            }
        else:
            # Для других моделей
            data = {
                "version": voice_id,
                "input": {
                    "text": text,
                    "speed": speed
                }
            }

        try:
            # Отправляем запрос на создание задачи
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            prediction = response.json()
            prediction_id = prediction["id"]

            # Ждем завершения задачи
            status_url = f"{self.api_url}/{prediction_id}"
            while True:
                response = requests.get(status_url, headers=headers)
                response.raise_for_status()

                prediction = response.json()
                status = prediction["status"]

                if status == "succeeded":
                    # Получаем URL аудио файла
                    audio_url = prediction["output"]

                    # Скачиваем аудио файл
                    audio_response = requests.get(audio_url)
                    audio_response.raise_for_status()

                    # Сохраняем в файл
                    with open(output_file, "wb") as f:
                        f.write(audio_response.content)

                    logger.info(f"Аудио успешно сгенерировано: {output_file}")
                    return output_file
                elif status == "failed":
                    error = prediction.get("error", "Неизвестная ошибка")
                    logger.error(f"Ошибка генерации аудио: {error}")
                    raise RuntimeError(f"Не удалось сгенерировать аудио: {error}")

                # Ждем перед следующей проверкой
                time.sleep(2)
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса к Replicate API: {str(e)}")
            raise RuntimeError(f"Не удалось сгенерировать аудио: {str(e)}")

    def get_available_voices(self) -> Dict[str, Any]:
        """
        Получает список доступных голосов

        Returns:
            Словарь с информацией о доступных голосах
        """
        # Для Replicate возвращаем предопределенный список моделей
        voices = [
            {"id": "suno-ai/bark", "name": "Bark (мультиязычная модель)"},
            {"id": "cjwbw/seamless-expressive", "name": "Seamless Expressive"},
            {"id": "lucataco/xtts-v2", "name": "XTTS v2"}
        ]

        return {"voices": voices}
