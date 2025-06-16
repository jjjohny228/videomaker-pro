import datetime
import os

import peewee as pw


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'video_editor.db')

# --- Database Setup (Example using SQLite) ---
db = pw.SqliteDatabase(DATABASE_PATH, pragmas={'foreign_keys': 1})


class _BaseModel(pw.Model):
    class Meta:
        database = db


# --- Constants for Choices ---

POSITION_CHOICES = [
    ('top_left', 'Top Left'), ('top_center', 'Top Center'), ('top_right', 'Top Right'),
    ('center', 'Center'),
    ('bottom_left', 'Bottom Left'), ('bottom_center', 'Bottom Center'), ('bottom_right', 'Bottom Right'),
]

CAPTION_FONT_CHOICES = [
    ('Arial', 'Arial'), ('Verdana', 'Verdana'), ('Tahoma', 'Tahoma'),
    ('Georgia', 'Georgia'), ('Times New Roman', 'Times New Roman'), ('Courier New', 'Courier New'),
    ('Impact', 'Impact'), ('Comic Sans MS', 'Comic Sans MS'), ('Roboto', 'Roboto'),
]

CAPTION_POSITION_CHOICES = [
    ('bottom_center', 'Bottom Center'), ('center', 'Center')
]

TTS_PROVIDER_CHOICES = [
    ('minimax', 'Minimax T2A Turbo'),
    ('replicate', 'Replicate (Cloned Voices)'),
]

class Voice(_BaseModel):
    """
    Stores voice settings for TTS.

    """
    provider = pw.CharField(choices=TTS_PROVIDER_CHOICES, help_text="TTS provider.")
    voice_id = pw.CharField(help_text="TTS provider-specific voice ID.")
    description = pw.CharField(null=True, help_text="User-friendly description of the voice.")
    speed = pw.FloatField(default=1.0, constraints=[pw.Check('speed >= 0.1 AND speed <= 5.0')], help_text="Voice speed (e.g., from 0.5 to 2.0).")

    class Meta:
        table_name = 'voices'
        constraints = [pw.SQL('UNIQUE (provider, voice_id)')]  # The pair (provider, voice_id) must be unique

    def __str__(self):
        provider_display = self.get_provider_display() if hasattr(self, 'get_provider_display') else self.provider
        return f"{provider_display} - ID: {self.voice_id}"


class BrandKit(_BaseModel):
    """
    Stores branding configurations, including visual elements,
    audio settings, and output preferences.
    """
    name = pw.CharField(unique=True, help_text="User-defined name for the brand kit.")
    intro_clip_path = pw.CharField(null=True,
                                   constraints=[
                                       pw.Check("intro_clip_path LIKE '%.mp4' OR intro_clip_path LIKE '%.mov' OR intro_clip_path LIKE '%.avi' OR intro_clip_path LIKE '%.mkv' OR intro_clip_path IS NULL")])
    randomize_clips = pw.BooleanField(default=False,
                                      help_text="If checked, clips from the kit will be used in random order.")

    watermark_path = pw.CharField(null=True,
                                  constraints=[
                                      pw.Check(
                                          "watermark_path LIKE '%.png' OR watermark_path LIKE '%.jpg' OR watermark_path LIKE '%.jpeg' OR watermark_path IS NULL")],
                                  help_text="Path to a 16:9 PNG watermark image with transparency.")
    watermark_position = pw.CharField(default="top_right", choices=POSITION_CHOICES,
                                      help_text="Position of the watermark on the screen.")
    watermark_width_persent = pw.IntegerField(default=50, help_text="Persent of the width to calculate watermark dimensions")
    avatar_path = pw.CharField(null=True,
                                    constraints=[
                                        pw.Check(
                                            "avatar_path LIKE '%.mp4' OR avatar_path LIKE '%.mov' OR avatar_path LIKE '%.avi' OR avatar_path LIKE '%.mkv' OR avatar_path IS NULL")
                                    ],
                                    help_text="Path to an animated looped avatar clip (e.g., talking head).")
    avatar_position = pw.CharField(default="bottom_left", choices=POSITION_CHOICES,
                                   help_text="Position of the avatar on the screen.")
    avatar_background_color = pw.CharField(null=True, max_length=6, help_text="Background color of the avatar video to cut out it (6 hex characters).",
                                           constraints=[pw.Check('LENGTH(avatar_background_color) = 6')])
    avatar_width_persent = pw.IntegerField(default=50, help_text="Persent of the width to calculate avatar dimensions")
    cta_path = pw.CharField(null=True,
                 constraints=[
                     pw.Check(
                         "cta_path LIKE '%.webm' OR cta_path LIKE '%.png' OR cta_path LIKE '%.gif' OR cta_path IS NULL")
                 ],
                 help_text="Path to a WebM/PNG subscribe call-to-action overlay with transparency.")
    cta_interval = pw.IntegerField(default=120,
                                             help_text="Interval (in seconds) for displaying the subscribe CTA overlay.")
    cta_position = pw.IntegerField(default="bottom_left", choices=POSITION_CHOICES,
                                   help_text="Position of the cta on the screen.")
    cta_width_persent = pw.IntegerField(default=50, help_text="Persent of the width to calculate cta dimensions")
    cta_duration = pw.IntegerField(default=60, help_text="Duration of the cta overlay.")
    voice = pw.ForeignKeyField(Voice, backref='used_by_brand_kits', null=True, on_delete='SET NULL',
                               help_text="Selected voice configuration for TTS.")

    aspect_ratio = pw.CharField(default="16:9", choices=[("16:9", "Landscape (16:9)"), ("9:16", "Portrait (9:16)")],
                                help_text="Aspect ratio for the output video.")
    music_path = pw.CharField(null=True, help_text="Path to the background music MP3 file.")
    music_volume = pw.IntegerField(default=20, constraints=[pw.Check('music_volume >= 0 AND music_volume <= 100')], help_text="Volume of the background music (from 0 to 100).")
    lut_path = pw.CharField(null=True,
                            help_text="Path to a LUT file for color grading (e.g., .cube). Applied to all clips except the intro.")
    mask_effect_path = pw.CharField(null=True,
                                    help_text="Path to a video/image file for a mask effect (e.g., sparks/smoke via alpha channel).")
    mask_effect_background_color = pw.CharField(null=True,
                                    help_text="Background color of the mask (6 hex characters).")
    transition_duration = pw.FloatField(default=0.5, help_text="Duration of the transition between clips (in seconds).")
    script_to_voice_over = pw.TextField(help_text="Script to voice over")
    language_code = pw.CharField(default="en", help_text="Language code for the brand kit (e.g., en, ru).")

    created_at = pw.DateTimeField(default=datetime.datetime.now, help_text="Date and time of record creation.")
    updated_at = pw.DateTimeField(default=datetime.datetime.now, help_text="Date and time of the last record update.")

    @property
    def auto_intro_settings(self):
        """ Property to access the auto-intro settings. """
        try:
            return AutoIntroSetting.get(AutoIntroSetting.brand_kit == self)
        except AutoIntroSetting.DoesNotExist:
            return None

    @property
    def caption_config(self):
        """ Property to access the caption specifications. """
        try:
            return Caption.get(Caption.brand_kit == self)
        except Caption.DoesNotExist:
            return None

    @property
    def transition_names(self):
        """
        Returns a list of the names of all transitions for this BrandKit.
        """
        return [t.name for t in
                Transition.select()
                .join(BrandKitTransition)
                .where(BrandKitTransition.brand_kit == self)]

    @property
    def source_videos_paths(self):
        """
        Returns a list of the paths of all source videos for this BrandKit.
        """
        return [t.path for t in self.source_videos]

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        super_save_result = super().save(*args, **kwargs)
        return super_save_result

    def __str__(self):
        return self.name

    class Meta:
        table_name = 'brand_kits'


# --- Model Definitions ---

class AutoIntroSetting(_BaseModel):
    """
    Settings for automatically generating an intro with a typewriter title.
    Intended for a One-to-One relationship with BrandKit.
    """
    brand_kit = pw.ForeignKeyField(BrandKit, backref='auto_intro_setting_ref', on_delete='CASCADE',
                                   help_text="The BrandKit these intro settings belong to.")
    text = pw.TextField(help_text="The intro text.")
    title_font = pw.CharField(default="Arial", choices=CAPTION_FONT_CHOICES, help_text="Font for the title.")
    title_font_size = pw.IntegerField(default=48, constraints=[pw.Check('title_font_size >= 8 AND title_font_size <= 200')], help_text="Font size for the title.")
    title_font_color = pw.CharField(default="FFFFFF", constraints=[pw.Check(
            "length(title_font_color) = 6 AND title_font_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'")],
                                    help_text="Hex color code for the title font (e.g., FFFFFF for white).")

    background_type = pw.CharField(
        default="color",
        choices=[('color', 'Color'), ('image', 'Image'), ('video', 'Video')],
        help_text="Type of background for the auto intro title."
    )
    background_value = pw.CharField(
        default="000000",
        help_text="Hex color code, or path to background image/video file."
    )
    duration = pw.IntegerField(default=5, help_text="Duration of the auto-intro title in seconds.")

    class Meta:
        table_name = 'auto_intro_settings'


class Caption(_BaseModel):
    """
    Styling for video captions.
    Intended for a One-to-One relationship with BrandKit.
    """
    brand_kit = pw.ForeignKeyField(BrandKit, backref='caption_specification', on_delete='CASCADE',
                                   help_text="The BrandKit these caption specifications belong to.", unique=True)
    font = pw.CharField(default="Arial", choices=CAPTION_FONT_CHOICES, help_text="Font for captions.")
    font_size = pw.IntegerField(default=24, help_text="Font size for captions.")
    font_color = pw.CharField(default="FFFFFF", constraints=[pw.Check(
            "length(font_color) = 6 AND font_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'")], help_text="Hex color code for caption font (e.g., FFFFFF for white).")
    stroke_width = pw.IntegerField(default=2, help_text="Stroke width for caption text.")
    stroke_color = pw.CharField(default="000000", constraints=[pw.Check(
            "length(stroke_color) = 6 AND stroke_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'")],
                                help_text="Hex color code for caption text stroke (e.g., 000000 for black).")
    position = pw.CharField(default="bottom_center", choices=CAPTION_POSITION_CHOICES,
                            help_text="Position of captions on the screen (9 grid options).")
    max_words_per_line = pw.IntegerField(default=7,  constraints=[pw.Check('max_words_per_line >= 1 AND max_words_per_line <= 20')], help_text="Maximum number of words per caption line.")

    class Meta:
        table_name = 'captions'


class Transition(_BaseModel):
    """ Defines an available video transition type. """
    TRANSITION_TYPE_CHOICES = [  # These values are used in FFmpeg xfade
        ('none', 'None'), ('fade', 'Fade'), ('dissolve', 'Dissolve'), ('pixelize', 'Pixelize'),
        ('radial', 'Radial'), ('hblur', 'Horizontal Blur'), ('distance', 'Distance'),
        ('wipeleft', 'Wipe Left'), ('wiperight', 'Wipe Right'), ('wipeup', 'Wipe Up'), ('wipedown', 'Wipe Down'),
        ('slideleft', 'Slide Left'), ('slideright', 'Slide Right'), ('slideup', 'Slide Up'),
        ('slidedown', 'Slide Down'),
        ('diagtl', 'Diagonal Top-Left'), ('diagtr', 'Diagonal Top-Right'),
        ('diagbl', 'Diagonal Bottom-Left'), ('diagbr', 'Diagonal Bottom-Right'),
        ('hlslice', 'Horizontal Slice'), ('hrslice', 'Horizontal Reverse Slice'),
        ('vuslice', 'Vertical Slice'), ('vdslice', 'Vertical Reverse Slice'),
        ('circlecrop', 'Circle Crop'), ('rectcrop', 'Rectangle Crop'),
        ('circleopen', 'Circle Open'), ('circleclose', 'Circle Close'),
        ('fadeblack', 'Fade to Black'), ('fadewhite', 'Fade to White'), ('fadegrays', 'Fade to Grays'),
    ]
    name = pw.CharField(unique=True, choices=TRANSITION_TYPE_CHOICES,
                        help_text="Identifier of the transition type for FFmpeg.")
    description = pw.CharField(null=True, help_text="User-friendly description of the transition type.")

    def __str__(self):
        return self.get_name_display() if hasattr(self, 'get_name_display') else self.name

    class Meta:
        table_name = 'transitions'


class BrandKitTransition(_BaseModel):
    """
    Junction table for the many-to-many relationship between BrandKit and Transition.
    """
    transition = pw.ForeignKeyField(Transition, backref='+',
                                    help_text="The selected transition type.")
    brand_kit = pw.ForeignKeyField(BrandKit, backref='selected_transitions_junction',
                                   help_text="The BrandKit for which this transition is selected.")

    class Meta:
        table_name = 'brand_kit_transitions'
        primary_key = pw.CompositeKey('brand_kit', 'transition')  # Ensures the (brand_kit, transition) pair is unique


class VoiceOverApiKey(_BaseModel):
    """
    Stores API keys for external services.
    This model stores them in plaintext for simplicity of this example.
    """
    provider = pw.CharField(choices=TTS_PROVIDER_CHOICES, help_text="Name of the TTS/AI service.")
    api_key = pw.CharField(unique=True, help_text="API Key (store encrypted in production!)")
    is_active = pw.BooleanField(default=True, help_text="Whether this API key is currently active.")
    group_id = pw.IntegerField(unique=False, help_text="Group ID for this API key.")

    def get_display_name(self):
        """ Returns a safe-to-display name for the key. """
        status_display = 'Active' if self.is_active else 'Inactive'
        return f"Key for {self.provider} ({status_display})"

    class Meta:
        table_name = 'voice_over_api_keys'


class AssemblyAiApiKey(_BaseModel):
    """
    Stores API keys for AssemblyAi.
    """
    api_key = pw.CharField(unique=True, help_text="API Key (store encrypted in production!)")
    is_active = pw.BooleanField(default=True, help_text="Whether this API key is currently active.")

    class Meta:
        table_name = 'assembly_api_keys'


class SourceVideos(_BaseModel):
    """
    This model stores videos for the brand kit.
    """
    brand_kit = pw.ForeignKeyField(BrandKit, backref='source_videos',
                                   help_text="The BrandKit for which this videos is selected.")
    path = pw.CharField(constraints=[pw.Check("path LIKE '%.mp4' OR path LIKE '%.mov' "
                                              "OR path LIKE '%.avi' OR path LIKE '%.mkv' "
                                              "OR path IS NULL")
                                     ],
                        help_text="Path to a video")

    class Meta:
        table_name = 'source_videos'


# --- DB Initialization Utility ---
def register_models() -> None:
    for model in _BaseModel.__subclasses__():
        model.create_table()


if __name__ == '__main__':
    db.connect(reuse_if_open=True)
    register_models()
