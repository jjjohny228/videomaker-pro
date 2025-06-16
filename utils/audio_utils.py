from mutagen import File

def get_audio_duration(audio_path: str) -> float:
    audiofile = File(audio_path)
    length = audiofile.info.length
    return length
