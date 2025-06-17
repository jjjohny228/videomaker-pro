import threading

from core import editor
from core.editor import VideoEditor

brand_kit = BrandKit.get(id=1)


async def test_video_editor():
    editor = VideoEditor(brand_kit)
    title = None  # Мне впадлу разбираться как загружаються данные, добавишь сам
    script = None
    editor.create_video(title, script)


class JobsHandler:
    def __init__(self, editor) -> None:
        self.handles = {}
        self.editor = editor

    def start_job(self, key: int, title, script):
        self.handles[key] = threading.Thread(self.editor.create_video, title, script)

    def end_job(self, key: int, title, script):
        self.handles[key].join()


if __name__ == "__main__":
    test_video_editor()
