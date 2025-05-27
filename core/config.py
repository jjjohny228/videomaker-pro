import sys


class Config:
    BACKGROUND_VIDEO_FOLDER = 'resource/background_videos'
    BACKGROUND_IMAGE_FOLDER = 'resource/background_images'
    COMMENTATOR = 'resource/chromakey_backgrounds/commentator.mp4'
    BACKGROUND_VIDEO = 'resource/background_videos/minecraft2.mov'
    BOTTOM_VIDEOS = 'resource/bottom_videos'
    BACKGROUND_IMAGE = 'resource/background_images/black.png'

    SOURCE_FOLDER = 'source'
    RESULT_FOLDER = 'result'
    TEMP_FOLDER = 'temp'

    OUTPUT_PTS = 30

    COMMENTATOR_COLOR = '0x05c803'

    # Improves rendering
    if sys.platform == 'darwin':
        VIDEO_CODEC = 'h264_videotoolbox'
    # Works only for amd
    elif sys.platform == 'win32':
        VIDEO_CODEC = 'h264_amf'
    else:
        VIDEO_CODEC = 'libx264'
