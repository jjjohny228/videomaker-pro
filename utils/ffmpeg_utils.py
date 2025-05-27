import subprocess
import json
import os
from typing import Dict, Any, Tuple
import logging
import re

from core.config import Config

logger = logging.getLogger(__name__)


class FFmpegUtils:
    def run_command(self, command: list) -> subprocess.CompletedProcess:
        """Выполняет команду FFmpeg"""
        logger.debug(f"Выполнение команды FFmpeg: {' '.join(command)}")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка выполнения команды FFmpeg: {e.stderr}")
            raise

    def get_video_info(self, video_path: str):
        # Get video information using ffprobe
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', text=True)
        info = json.loads(result.stdout)

        # Extract video dimensions
        video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        duration = float(video_stream['duration'])

        return width, height, duration

    def get_video_duration(self, video_path):
        """Get the duration of the video in seconds."""
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)


    def create_transition(self, clip1: str, clip2: str, output: str,
                          transition_type: str = "fade", duration: float = 0.5) -> str:
        """
        Creates a transition between two clips with support for various transition types

        """
        # Tuple of supported transition types
        supported_transitions = (
            'fade', 'dissolve', 'pixelize', 'radial', 'hblur', 'distance',
            'wipeleft', 'wiperight', 'wipeup', 'wipedown',
            'slideleft', 'slideright', 'slideup', 'slidedown',
            'diagtl', 'diagtr', 'diagbl', 'diagbr',
            'hlslice', 'hrslice', 'vuslice', 'vdslice',
            'circlecrop', 'rectcrop', 'circleopen', 'circleclose',
            'fadeblack', 'fadewhite', 'fadegrays'
        )

        # Check if the transition type is supported
        if transition_type not in supported_transitions:
            raise ValueError(f"Unsupported transition type: {transition_type}. "
                             f"Available: {', '.join(supported_transitions)}")

        # Get the duration of the first clip
        clip1_duration = self.get_video_duration(clip1)

        # Check that the transition duration does not exceed the clip duration
        if duration >= clip1_duration:
            raise ValueError(f"Transition duration ({duration}s) cannot be greater than or equal to "
                             f"the duration of the first clip ({clip1_duration}s)")

        # Use the transition name directly for FFmpeg
        ffmpeg_transition = transition_type

        fps = Config.OUTPUT_PTS

        # Create the filter for the transition
        filter_complex = (
            f"[0:v]trim=0:{clip1_duration - duration},setpts=PTS-STARTPTS[v0];"
            f"[0:v]trim={clip1_duration - duration}:{clip1_duration},setpts=PTS-STARTPTS,fps={fps},settb=AVTB[v1];"
            f"[1:v]trim=0:{duration},setpts=PTS-STARTPTS,fps={fps},settb=AVTB[v2];"
            f"[1:v]trim={duration},setpts=PTS-STARTPTS[v3];"
            f"[v1][v2]xfade=transition={ffmpeg_transition}:duration={duration}:offset=0,format=yuv420p[xf];"
            f"[v0][xf][v3]concat=n=3:v=1:a=0[outv]"
        )

        # Combine video filters (audio is not processed in this specific filter_complex)
        full_filter = f"{filter_complex}"

        # Execute the FFmpeg command
        cmd = [
            'ffmpeg',
            "-i", clip1,
            "-i", clip2,
            "-filter_complex", full_filter,
            "-map", "[outv]",
            "-c:v", Config.VIDEO_CODEC,
            "-c:a", "aac", # Audio codec is specified, though not processed by filter_complex
            "-y",
            output
        ]

        try:
            self.run_command(cmd)
            return output
        except Exception as e:
            raise RuntimeError(f"Error creating transition: {str(e)}")


