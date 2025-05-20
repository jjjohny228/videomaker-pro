import threading
import queue
from typing import Dict, Any, Callable, List, Optional
import logging
import time

from models.job import Job, JobStatus

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self, max_workers: int = 2):
        self.queue = queue.Queue()
        self.jobs = {}  # Словарь для хранения информации о задачах
        self.max_workers = max_workers
        self.workers = []
        self.running = False
        self.lock = threading.Lock()  # Блокировка для безопасного доступа к словарю jobs

    def start(self):
        """Запускает обработку очереди задач"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        logger.info(f"Запущено {self.max_workers} рабочих потоков")

    def stop(self):
        """Останавливает обработку очереди задач"""
        self.running = False
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        logger.info("Все рабочие потоки остановлены")

    def add_job(self, job_id: str, job_func: Callable, job_args: Dict[str, Any],
                callback: Optional[Callable] = None) -> str:
        """
        Добавляет задачу в очередь

        Args:
            job_id: Идентификатор задачи
            job_func: Функция для выполнения
            job_args: Аргументы функции
            callback: Функция обратного вызова для отслеживания прогресса

        Returns:
            Идентификатор задачи
        """
        with self.lock:
            # Создаем объект задачи
            job = Job(
                job_id=job_id,
                title=job_args.get("title", ""),
                script=job_args.get("script", ""),
                brand_kit_id=job_args.get("brand_kit_id", "")
            )
            self.jobs[job_id] = job

        # Добавляем задачу в очередь
        self.queue.put((job_id, job_func, job_args, callback))
        logger.info(f"Задача {job_id} добавлена в очередь")
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Получает статус задачи

        Args:
            job_id: Идентификатор задачи

        Returns:
            Словарь с информацией о задаче
        """
        with self.lock:
            if job_id not in self.jobs:
                return {"status": "not_found"}
            return self.jobs[job_id].to_dict()

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Получает информацию о всех задачах

        Returns:
            Список словарей с информацией о задачах
        """
        with self.lock:
            return [job.to_dict() for job in self.jobs.values()]

    def _worker_loop(self):
        """Функция рабочего потока"""
        while self.running:
            try:
                # Получаем задачу из очереди с таймаутом
                job_id, job_func, job_args, callback = self.queue.get(timeout=1.0)

                # Обновляем статус задачи
                with self.lock:
                    if job_id in self.jobs:
                        self.jobs[job_id].mark_as_processing()

                # Создаем функцию обратного вызова для отслеживания прогресса
                def progress_callback(percentage, message):
                    with self.lock:
                        if job_id in self.jobs:
                            self.jobs[job_id].update_progress(percentage, message)
                    if callback:
                        callback(percentage, message)

                try:
                    # Выполняем функцию задачи
                    result = job_func(**job_args, progress_callback=progress_callback)

                    # Обновляем статус задачи
                    with self.lock:
                        if job_id in self.jobs:
                            self.jobs[job_id].mark_as_completed(result)

                    logger.info(f"Задача {job_id} успешно выполнена")

                except Exception as e:
                    logger.exception(f"Ошибка выполнения задачи {job_id}: {str(e)}")

                    # Обновляем статус задачи
                    with self.lock:
                        if job_id in self.jobs:
                            self.jobs[job_id].mark_as_failed(str(e))

                finally:
                    self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.exception(f"Неожиданная ошибка в рабочем потоке: {str(e)}")
