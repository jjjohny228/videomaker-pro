import logging
import time

from database.models import BrandKit
from utils.ffmpeg_utils import FFmpegUtils
from utils.audio_utils import get_audio_duration
from core.config import Config

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, brand_kit: BrandKit):
        self.brand_kit = brand_kit
        self.ffmpeg = FFmpegUtils()
        self.temp_dir = Config.TEMP_FOLDER

    def add_audio_in_video(self, video_path: str, voice_path: str) -> str:
        """
        Replaces the audio track in a video with the provided audio.

        """
        output_path = f'{self.temp_dir}/{int(time.time())}misic_added.mp4'
        if self.brand_kit.music_path:
            audio_path = self._mix_audio_with_music(voice_path)
        else:
            audio_path = voice_path
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-map", "0:v",
            "-map", "1:a",
            "-y", output_path
        ]
        self.ffmpeg.run_command(cmd)
        return output_path

    def _mix_audio_with_music(self, voice_path: str) -> str:
        """
        Mixes TTS voice audio with background music. Loops music if it's shorter than the voice.

        """
        output_path = f'{self.temp_dir}/{int(time.time())}_audio_music.mp3'
        music_path = self.brand_kit.music_path
        music_volume = self.brand_kit.music_volume / 100

        voice_duration = get_audio_duration(voice_path)
        music_duration = get_audio_duration(music_path)

        if music_duration < voice_duration:
            # Loop and trim music if it's shorter than voice
            cmd = [
                "ffmpeg",
                "-i", voice_path,
                "-stream_loop", "-1",  # Infinite loop for music
                "-i", music_path,
                "-filter_complex",
                f"[1:a]volume={music_volume},atrim=0:{voice_duration}[bg];[0:a][bg]amix=inputs=2:duration=first",
                "-y", output_path
            ]
        else:
            # Trim music if it's longer than voice
            cmd = [
                "ffmpeg",
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex",
                f"[1:a]volume={music_volume},atrim=0:{voice_duration}[bg];[0:a][bg]amix=inputs=2:duration=first",
                "-y", output_path
            ]

        self.ffmpeg.run_command(cmd)
        return output_path
