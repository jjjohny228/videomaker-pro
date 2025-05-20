from enum import Enum
from typing import Dict, Any, Optional
import time
from datetime import datetime


class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    def __init__(self, job_id: str, title: str, script: str, brand_kit_id: str):
        self.job_id = job_id
        self.title = title
        self.script = script
        self.brand_kit_id = brand_kit_id
        self.status = JobStatus.QUEUED
        self.progress = 0
        self.message = "Задача в очереди"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None

    def update_progress(self, progress: int, message: str):
        """Обновляет прогресс выполнения задачи"""
        self.progress = progress
        self.message = message
        self.updated_at = datetime.now()

    def mark_as_processing(self):
        """Отмечает задачу как обрабатываемую"""
        self.status = JobStatus.PROCESSING
        self.message = "Задача обрабатывается"
        self.updated_at = datetime.now()

    def mark_as_completed(self, result: str):
        """Отмечает задачу как завершенную"""
        self.status = JobStatus.COMPLETED
        self.progress = 100
        self.message = "Задача завершена"
        self.result = result
        self.updated_at = datetime.now()
        self.completed_at = datetime.now()

    def mark_as_failed(self, error: str):
        """Отмечает задачу как неудачную"""
        self.status = JobStatus.FAILED
        self.message = f"Ошибка: {error}"
        self.error = error
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь"""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "brand_kit_id": self.brand_kit_id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
