import os
import logging
import argparse
import sys
from typing import Dict, Any

from core.config import Config
from core.editor import VideoEditor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("video_editor.log")
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Точка входа в приложение"""
    parser = argparse.ArgumentParser(description="Автоматический редактор видео")
    parser.add_argument("--config", type=str, default="config.ini", help="Путь к файлу конфигурации")
    parser.add_argument("--title", type=str, help="Заголовок видео")
    parser.add_argument("--script", type=str, help="Путь к файлу со скриптом")
    parser.add_argument("--brand-kit", type=str, help="Идентификатор набора брендинга")
    parser.add_argument("--output", type=str, help="Путь к выходному файлу")

    args = parser.parse_args()

    try:
        # Инициализируем редактор видео
        editor = VideoEditor(args.config)

        # Если указаны все необходимые аргументы, создаем видео
        if args.title and args.script and args.brand_kit:
            # Загружаем скрипт из файла
            if os.path.exists(args.script):
                with open(args.script, "r", encoding="utf-8") as f:
                    script_text = f.read()
            else:
                script_text = args.script

            # Создаем видео
            job_id = editor.create_video(
                title=args.title,
                script=script_text,
                brand_kit_id=args.brand_kit,
                callback=lambda progress, message: print(f"Прогресс: {progress}% - {message}")
            )

            # Запускаем обработку очереди
            editor.job_manager.start()

            # Ждем завершения задачи
            while True:
                status = editor.get_job_status(job_id)
                if status["status"] in ["completed", "failed"]:
                    break
                import time
                time.sleep(1)

            # Выводим результат
            if status["status"] == "completed":
                print(f"Видео успешно создано: {status['result']}")
                if args.output:
                    import shutil
                    shutil.copy(status["result"], args.output)
                    print(f"Видео сохранено в: {args.output}")
            else:
                print(f"Ошибка создания видео: {status['error']}")

            # Останавливаем обработку очереди
            editor.job_manager.stop()
        else:
            print("Для создания видео необходимо указать заголовок, скрипт и набор брендинга")
            print("Пример: python main.py --title 'Мое видео' --script 'script.txt' --brand-kit 'default'")

    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {str(e)}")
        print(f"Произошла ошибка: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
