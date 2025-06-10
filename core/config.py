import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    SOURCE_FOLDER = 'source'
    RESULT_FOLDER = 'result'
    TEMP_FOLDER = 'temp'

    OUTPUT_PTS = 30

    # Improves rendering
    if sys.platform == 'darwin':
        VIDEO_CODEC = 'h264_videotoolbox'
    # Works only for amd
    elif sys.platform == 'win32':
        VIDEO_CODEC = 'h264_amf'
    else:
        VIDEO_CODEC = 'libx264'

    SUPPORTED_TRANSITIONS = (
            'fade', 'dissolve', 'pixelize', 'radial', 'hblur', 'distance',
            'wipeleft', 'wiperight', 'wipeup', 'wipedown',
            'slideleft', 'slideright', 'slideup', 'slidedown',
            'diagtl', 'diagtr', 'diagbl', 'diagbr',
            'hlslice', 'hrslice', 'vuslice', 'vdslice',
            'circlecrop', 'rectcrop', 'circleopen', 'circleclose',
            'fadeblack', 'fadewhite', 'fadegrays'
        )

    MINIMAX_MODEL = 'speech-02-turbo'
