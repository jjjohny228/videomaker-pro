from services.brand_kit_service import BrandKitService
from processors.video_processor import VideoProcessor
from processors.audio_processor import AudioProcessor
from processors.caption_processor import CaptionProcessor
from database.models import BrandKit

class VideoEditor:
    def __init__(self, brandkit_name):
        self.brandkit = BrandKit.get(BrandKit.name == brandkit_name)
        self.video_processor = VideoProcessor(self.brandkit)
        self.audio_processor = AudioProcessor(self.brandkit)
        self.caption_processor = CaptionProcessor(self.brandkit)

    def create_video(self, title, script, callback=None):
        intro_clip = self.brandkit.intro_clip_path
        watermark = self.brandkit.watermark_path
        watermark_pos = self.brandkit.watermark_position
        avatar = self.brandkit.avatar_clip_path
        avatar_pos = self.brandkit.avatar_position
        avatar_bg = self.brandkit.avatar_background_color
        cta = self.brandkit.cta_path
        cta_pos = self.brandkit.cta_position
        cta_interval = self.brandkit.cta_interval
        music = self.brandkit.music_path
        music_vol = self.brandkit.music_volume
        lut = self.brandkit.lut_path
        mask = self.brandkit.mask_effect_path
        aspect = self.brandkit.aspect_ratio
        transition_duration = self.brandkit.transition_duration
        randomize = self.brandkit.randomize_clips

        auto_intro = self.brandkit.auto_intro_settings
        caption = self.brandkit.caption_config
        voice = self.brandkit.voice
        transitions = [bt.transition for bt in self.brandkit.brandkittransition_set]

        tts_audio = self.audio_processor.generate_tts(script, voice)
        tts_audio_duration = self.audio_processor.get_audio_length(tts_audio)

        if intro_clip:
            intro_path = intro_clip
        elif auto_intro and auto_intro.enabled:
            intro_path = self.video_processor.create_intro(title, auto_intro)
        else:
            intro_path = None

        content_clips = self._get_content_clips(randomize)
        transition_types = [t.name for t in transitions]
        content_video = self.video_processor.prepare_content_clips(content_clips, transition_types, transition_duration, duration=tts_audio_duration)

        # Apply LUT and mask only to content video (not intro)
        processed_content = content_video
        if lut:
            processed_content = self.video_processor.apply_lut(processed_content, lut)
        if mask:
            processed_content = self.video_processor.apply_mask(processed_content, mask)

        # Concatenate intro and processed content
        if intro_path:
            full_video = self.video_processor.concat_videos([intro_path, processed_content])
        else:
            full_video = processed_content

        captioned_video = self.caption_processor.add_captions(full_video, tts_audio)
        audio_video = self.audio_processor.mix_audio_with_music(tts_audio, music, music_vol)
        final_audio_video = self.audio_processor.replace_audio_in_video(captioned_video, audio_video)
        finalized_video = self.video_processor.finalize_video(final_audio_video, aspect)

        overlays = {
            'avatar': avatar,
            'avatar_position': avatar_pos,
            'avatar_bg_color': avatar_bg,
            'watermark': watermark,
            'watermark_position': watermark_pos,
            'cta': cta,
            'cta_position': cta_pos,
            'cta_interval': cta_interval,
        }
        final_video = self.video_processor.add_overlays(finalized_video, overlays)
        return final_video

    def _get_content_clips(self, randomize):
        # Example: get all content clips from BrandKit, optionally shuffle
        clips = [clip.file_path for clip in self.brandkit.content_clips]
        if randomize:
            import random
            random.shuffle(clips)
        return clips
