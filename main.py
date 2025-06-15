import logging
import sys

import tkinter as tk
from ui.brand_kit_manager import VideoEditorMaxApp

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
    root = tk.Tk()
    app = VideoEditorMaxApp(root)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
