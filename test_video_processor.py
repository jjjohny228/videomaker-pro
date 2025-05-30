from processors.video_processor import VideoProcessor

def test_prepare_content_clips():
    videos = ['tests/0724.mov', 'tests/0724.mov', 'tests/ssstik.io_@movie.mafia2_1748542876264.mp4']
    transitions = ['fade', 'dissolve', 'pixelize', 'radial']
    test_video = VideoProcessor({'target_resolution': '1080:1920'}, videos, transitions)
    test_video.prepare_content_clips(videos, transitions, 'tests')

def test_create_intro():
    test_video = VideoProcessor({'target_resolution': '1080:1920'})
    test_video.create_intro('this is a big intro', {}, 'tests')

def test_add_overlays():
    test_video = VideoProcessor({'target_resolution': '1080:1920'})
    test_video.add_overlays('tests/content_with_transitions.mp4',
                            {'watermark_width': 3, 'watermark_position': 'top-left', 'avatar': 'resource/commentators/0530.mov',
                             'avatar_position': 'bottom-right', 'avatar_width': 1,
                             'avatar_bg_color': '02ff07', 'cta': 'resource/cta/cta1.png', 'cta_width': 1, 'watermark': 'resource/logos/logo1.png'},
                            'tests')

def test_apply_effects():
    test_video = VideoProcessor({'target_resolution': '1080:1920'})
    test_video.apply_effects('tests/overlays.mp4', {'mask_bg_color': '179a13', 'mask': 'resource/masks/52039-467145237.mp4'}, 'tests')
if __name__ == '__main__':
    test_apply_effects()
