import os
import subprocess
import tempfile
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EdgeTTS:
    def __init__(self):
        # Проверяем, установлен ли edge-tts
        try:
            subprocess.run(["edge-tts", "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("edge-tts не установлен. Устанавливаем...")
            try:
                subprocess.run(["pip", "install", "edge-tts"], check=True)
            except subprocess.SubprocessError as e:
                logger.error(f"Не удалось установить edge-tts: {str(e)}")

    def generate_audio(self, text: str, voice_id: str = "", speed: float = 1.0, output_file: str = "") -> str:
        """
        Генерирует аудио из текста с помощью Edge TTS

        Args:
            text: Текст для преобразования в речь
            voice_id: Идентификатор голоса (если пустой, используется голос по умолчанию)
            speed: Скорость речи (1.0 = нормальная)
            output_file: Путь к выходному файлу

        Returns:
            Путь к сгенерированному аудио файлу
        """
        if not output_file:
            output_file = tempfile.mktemp(suffix=".mp3")

        # Если voice_id не указан, используем голос по умолчанию
        if not voice_id:
            voice_id = "ru-RU-SvetlanaNeural"  # Русский голос по умолчанию

        # Формируем команду
        cmd = [
            "edge-tts",
            "--voice", voice_id,
            "--rate", f"{int((speed - 1.0) * 100)}%",
            "--text", text,
            "--write-media", output_file
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Аудио успешно сгенерировано: {output_file}")
            return output_file
        except subprocess.SubprocessError as e:
            logger.error(f"Ошибка генерации аудио: {str(e)}")
            raise RuntimeError(f"Не удалось сгенерировать аудио: {str(e)}")

    def get_available_voices(self) -> dict:
        """
        Получает список доступных голосов

        Returns:
            Словарь с информацией о доступных голосах
        """
        try:
            result = subprocess.run(["edge-tts", "--list-voices"], capture_output=True, text=True, check=True)
            voices = []

            for line in result.stdout.splitlines():
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    voice_id = parts[0]
                    name = " ".join(parts[1:])
                    voices.append({"id": voice_id, "name": name})

            return {"voices": voices}
        except subprocess.SubprocessError as e:
            logger.error(f"Ошибка получения списка голосов: {str(e)}")
            return {"voices": []}
