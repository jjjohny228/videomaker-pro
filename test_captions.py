import os
import subprocess
import time

from core.config import Config
from processors.caption_processor import CaptionProcessor
from database.models import BrandKit


def test_add_captions():
    ass_file = 'temp/1749983474_subtitles.ass'
    output_file = os.path.join('temp', f"{int(time.time())}_captioned.mp4")
    cmd = [
        "ffmpeg",
        "-i", 'tests/videos/ssstik.io_@movie.mafia2_1748542876264.mp4',
        "-vf", f"ass={ass_file}",
        "-c:v", Config.VIDEO_CODEC,
        "-c:a", "copy",
        "-y",
        output_file
    ]
    subprocess.run(cmd, check=True)
    return output_file


def test_caption_processor():
    brand_kit = BrandKit.get(id=1)
    caption_processor = CaptionProcessor(brand_kit)
    caption_processor.add_captions('tests/other/clone_source.mp3',
                                   'tests/videos/ssstik.io_@movie.mafia2_1748542876264.mp4')


if __name__ == '__main__':
    # test_add_captions()
    test_caption_processor()
