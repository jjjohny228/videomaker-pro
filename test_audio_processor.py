from database.models import BrandKit
from processors.audio_processor import AudioProcessor


def test_audio_processor():
    brand_kit = BrandKit.get(id=1)
    caption_processor = AudioProcessor(brand_kit)
    caption_processor.add_audio_in_video('tests/videos/ssstik.io_@movie.mafia2_1748542876264.mp4',
                                         'tests/other/voice_track.mp3')


if __name__ == '__main__':
    test_audio_processor()
