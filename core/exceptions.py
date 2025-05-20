class VideoEditorError(Exception):
    """Базовый класс для всех исключений редактора видео"""
    pass

class ConfigError(VideoEditorError):
    """Ошибка конфигурации"""
    pass

class FFmpegError(VideoEditorError):
    """Ошибка FFmpeg"""
    pass

class TTSError(VideoEditorError):
    """Ошибка TTS сервиса"""
    pass

class ProcessingError(VideoEditorError):
    """Ошибка обработки видео"""
    pass

class ValidationError(VideoEditorError):
    """Ошибка валидации входных данных"""
    pass

class ResourceError(VideoEditorError):
    """Ошибка доступа к ресурсам"""
    pass

class QueueError(VideoEditorError):
    """Ошибка очереди задач"""
    pass

class JobError(VideoEditorError):
    """Ошибка выполнения задачи"""
    pass

class StorageError(VideoEditorError):
    """Ошибка хранилища"""
    pass
