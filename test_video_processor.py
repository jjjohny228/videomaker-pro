from processors.video_processor import VideoProcessor
from database.models import BrandKit

brand_kit = BrandKit.get(id=1)

def test_join_clips_with_transitions():
    test_video = VideoProcessor(brand_kit)
    test_video.join_clips_with_transitions()

def test_add_overlays():
    test_video = VideoProcessor(brand_kit)
    test_video.add_overlays('tests/videos/ssstik.io_@movie.mafia2_1748542876264.mp4')

def test_apply_effects():
    test_video = VideoProcessor(brand_kit)
    test_video.apply_effects('tests/videos/ssstik.io_@movie.mafia2_1748542876264.mp4')

def test_finalize_video():
    test_video = VideoProcessor(brand_kit)
    test_video.finalize_video('tests/effects.mp4', {'aspect_ratio': '9:16'}, 'tests/result.mov')
if __name__ == '__main__':
    test_apply_effects()
