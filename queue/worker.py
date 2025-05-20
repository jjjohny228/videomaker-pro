import threading
import logging
import time
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Worker(threading.Thread):
    """
    Рабочий поток для обработки задач из очереди
    """

    def __init__(self, worker_id: int, get_task_func: Callable,
                 task_complete_func: Callable, stop_event: threading.Event):
        """
        Инициализирует рабочий поток

        Args:
            worker_id: Идентификатор рабочего потока
            get_task_func: Функция для получения задачи из очереди
            task_complete_func: Функция для уведомления о завершении задачи
            stop_event: Событие для остановки рабочего потока
        """
        super().__init__(name=f"Worker-{worker_id}")
        self.worker_id = worker_id
        self.get_task_func = get_task_func
        self.task_complete_func = task_complete_func
        self.stop_event = stop_event
        self.daemon = True

    def run(self):
        """Основной цикл рабочего потока"""
        logger.info(f"Рабочий поток {self.worker_id} запущен")

        while not self.stop_event.is_set():
            try:
                # Получаем задачу из очереди
                task = self.get_task_func()

                if task is None:
                    # Если задач нет, ждем немного и продолжаем
                    time.sleep(0.5)
                    continue

                job_id, job_func, job_args, callback = task

                logger.info(f"Рабочий поток {self.worker_id} начал обработку задачи {job_id}")

                try:
                    # Выполняем задачу
                    result = job_func(**job_args, progress_callback=callback)

                    # Уведомляем о завершении задачи
                    self.task_complete_func(job_id, True, result)

                    logger.info(f"Рабочий поток {self.worker_id} успешно завершил задачу {job_id}")

                except Exception as e:
                    logger.exception(
                        f"Рабочий поток {self.worker_id} столкнулся с ошибкой при обработке задачи {job_id}: {str(e)}")

                    # Уведомляем об ошибке
                    self.task_complete_func(job_id, False, None, str(e))

            except Exception as e:
                logger.exception(f"Неожиданная ошибка в рабочем потоке {self.worker_id}: {str(e)}")
                time.sleep(1)  # Предотвращаем слишком частые ошибки

        logger.info(f"Рабочий поток {self.worker_id} остановлен")
