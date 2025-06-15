import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from services.brand_kit_service import BrandKitService

# --- Constants ---
POSITION_CHOICES = [
    ('top_left', 'Top Left'), ('top_center', 'Top Center'), ('top_right', 'Top Right'),
    ('middle_left', 'Middle Left'), ('middle_center', 'Middle Center'), ('middle_right', 'Middle Right'),
    ('bottom_left', 'Bottom Left'), ('bottom_center', 'Bottom Center'), ('bottom_right', 'Bottom Right'),
]
TTS_PROVIDER_CHOICES = [
    ('edge_tts', 'Edge-TTS (Free Tier)'),
    ('minimax_t2a_turbo', 'Minimax T2A Turbo'),
    ('replicate', 'Replicate (Cloned Voices)'),
]
CAPTION_FONT_CHOICES = [
    'Arial', 'Verdana', 'Tahoma', 'Georgia', 'Times New Roman', 'Courier New',
    'Impact', 'Comic Sans MS', 'Roboto'
]
TRANSITION_TYPE_CHOICES = [
    'none', 'fade', 'dissolve', 'pixelize', 'radial', 'hblur', 'distance', 'wipeleft', 'wiperight', 'wipeup',
    'wipedown', 'slideleft', 'slideright', 'slideup', 'slidedown', 'diagtl', 'diagtr', 'diagbl', 'diagbr',
    'hlslice', 'hrslice', 'vuslice', 'vdslice', 'circlecrop', 'rectcrop', 'circleopen', 'circleclose',
    'fadeblack', 'fadewhite', 'fadegrays'
]

# Тестовые данные для других компонентов (не Brand Kit)
API_KEYS = [
    {'service': 'edge_tts', 'key': 'sk-xxxx', 'active': True},
    {'service': 'replicate', 'key': 'sk-yyyy', 'active': False}
]
JOBS = [
    {'title': 'Short #1', 'status': 'Processing', 'progress': 50},
    {'title': 'Short #2', 'status': 'Queued', 'progress': 0},
]

try:
    from tkmacosx import Button as MacButton

    USE_MAC_BUTTON = True
except ImportError:
    USE_MAC_BUTTON = False


# --- Error Display Widget ---
class ErrorDisplay(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ffebee", relief="solid", bd=1)
        self.error_label = tk.Label(self, text="", fg="#c62828", bg="#ffebee", font=("Arial", 10), wraplength=600)
        self.error_label.pack(padx=10, pady=5)
        self.close_btn = ttk.Button(self, text="×", width=3, command=self.hide)
        self.close_btn.pack(side="right", padx=5)
        self.hide()

    def show_error(self, message):
        self.error_label.config(text=f"Ошибка: {message}")
        self.pack(fill="x", padx=10, pady=5)

    def hide(self):
        self.pack_forget()


# --- Scrollable Frame ---
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        vscrollbar = ttk.Scrollbar(self, orient="vertical")
        vscrollbar.pack(fill="y", side="right", expand=False)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscrollbar.config(command=canvas.yview)
        self.interior = interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor="nw")

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)


# --- SimpleTable ---
class SimpleTable(tk.Frame):
    def __init__(self, parent, columns, data, actions=None, action_callbacks=None):
        super().__init__(parent, bg="#262626")
        self.columns = columns
        self.data = data
        self.actions = actions or []
        self.action_callbacks = action_callbacks or []
        self._build_ui()

    def _build_ui(self):
        for idx in range(len(self.columns) + (1 if self.actions else 0)):
            self.grid_columnconfigure(idx, weight=1)
        # Заголовки
        for idx, text in enumerate(self.columns):
            tk.Label(self, text=text.capitalize(), fg="#fff", bg="#262626", font=("Arial", 12, "bold"),
                     padx=10, pady=8, anchor="w").grid(row=0, column=idx, sticky="nsew", padx=1, pady=(0, 2))
        if self.actions:
            tk.Label(self, text="Actions", fg="#fff", bg="#262626", font=("Arial", 12, "bold"),
                     padx=10, pady=8, anchor="w").grid(row=0, column=len(self.columns), sticky="nsew", padx=1,
                                                       pady=(0, 2))
        # Данные
        self.rows = []
        for row_idx, item in enumerate(self.data):
            widgets = []
            for col_idx, col in enumerate(self.columns):
                val = item.get(col, "")
                if col == "active" and isinstance(val, bool):
                    val = "Yes" if val else "No"
                lbl = tk.Label(self, text=str(val), fg="#fff", bg="#222", font=("Arial", 12), anchor="w")
                lbl.grid(row=row_idx + 1, column=col_idx, sticky="nsew", padx=1, pady=1)
                widgets.append(lbl)
            if self.actions:
                btn_frame = tk.Frame(self, bg="#222")
                btn_frame.grid(row=row_idx + 1, column=len(self.columns), sticky="nsew", padx=1, pady=1)
                for act, cb in zip(self.actions, self.action_callbacks):
                    ttk.Button(
                        btn_frame,
                        text=act,
                        command=lambda i=row_idx, c=cb: c(i),
                        width=7
                    ).pack(side="left", padx=2)
                widgets.append(btn_frame)
            self.rows.append(widgets)

    def refresh(self, new_data):
        self.data = new_data
        for widgets in self.rows:
            for w in widgets:
                w.destroy()
        self.rows.clear()
        self._build_ui()


# --- BrandKitEditor ---
class BrandKitEditor(tk.Toplevel):
    def __init__(self, master, brand_kit_service, brand_kit_name=None):
        super().__init__(master)
        self.title("BrandKit Editor")
        self.geometry("900x700")
        self.resizable(True, True)
        self.brand_kit_service = brand_kit_service
        self.brand_kit_name = brand_kit_name
        self.is_edit_mode = brand_kit_name is not None

        # Error display
        self.error_display = ErrorDisplay(self)

        # Load data if editing
        self.brand_kit_data = None
        if self.is_edit_mode:
            self.load_brand_kit_data()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_basic = ScrollableFrame(self.notebook)
        self.tab_effects = ScrollableFrame(self.notebook)
        self.tab_captions = ScrollableFrame(self.notebook)
        self.tab_script = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_basic, text="Basic")
        self.notebook.add(self.tab_effects, text="Effects")
        self.notebook.add(self.tab_captions, text="Captions")
        self.notebook.add(self.tab_script, text="Script")

        # Initialize variables
        self.init_variables()

        self.build_basic_tab(self.tab_basic.interior)
        self.build_effects_tab(self.tab_effects.interior)
        self.build_captions_tab(self.tab_captions.interior)
        self.build_script_tab(self.tab_script)

    def load_brand_kit_data(self):
        try:
            self.brand_kit_data = self.brand_kit_service.load_brand_kit(self.brand_kit_name)
            if not self.brand_kit_data:
                self.error_display.show_error(f"Не удалось загрузить Brand Kit '{self.brand_kit_name}'")
        except Exception as e:
            self.error_display.show_error(f"Ошибка загрузки Brand Kit: {str(e)}")

    def init_variables(self):
        # Basic variables
        self.name_var = tk.StringVar()
        self.aspect_ratio_var = tk.StringVar(value="16:9")
        self.randomize_clips_var = tk.BooleanVar()
        self.voice_var = tk.StringVar()

        # Watermark variables
        self.watermark_path_var = tk.StringVar()
        self.watermark_position_var = tk.StringVar(value="top_right")

        # Avatar variables
        self.avatar_path_var = tk.StringVar()
        self.avatar_position_var = tk.StringVar(value="bottom_left")
        self.avatar_background_color_var = tk.StringVar()

        # CTA variables
        self.cta_path_var = tk.StringVar()
        self.cta_position_var = tk.StringVar(value="bottom_center")
        self.cta_interval_var = tk.IntVar(value=120)

        # Music variables
        self.music_path_var = tk.StringVar()
        self.music_volume_var = tk.IntVar(value=20)

        # Effects variables
        self.lut_path_var = tk.StringVar()
        self.mask_path_var = tk.StringVar()
        self.mask_color_var = tk.StringVar(value="#000000")
        self.transition_duration_var = tk.DoubleVar(value=0.5)

        # Intro variables
        self.custom_intro_var = tk.BooleanVar(value=False)
        self.intro_file_var = tk.StringVar()
        self.title_font_var = tk.StringVar(value="Arial")
        self.title_font_size_var = tk.IntVar(value=48)
        self.title_font_color_var = tk.StringVar(value="FFFFFF")
        self.bg_type_var = tk.StringVar(value="color")
        self.bg_value_var = tk.StringVar(value="000000")

        # Caption variables
        self.caption_font_var = tk.StringVar(value="Arial")
        self.caption_font_size_var = tk.IntVar(value=24)
        self.caption_font_color_var = tk.StringVar(value="FFFFFF")
        self.caption_stroke_width_var = tk.IntVar(value=2)
        self.caption_stroke_color_var = tk.StringVar(value="000000")
        self.caption_position_var = tk.StringVar(value="bottom_center")
        self.caption_max_words_var = tk.IntVar(value=7)

        # Script variable
        self.script_var = tk.StringVar()

        # Transition variables
        self.transition_vars = {}
        for t in TRANSITION_TYPE_CHOICES:
            self.transition_vars[t] = tk.BooleanVar(value=False)

        # Load existing data if editing
        if self.brand_kit_data:
            self.populate_fields()

    def populate_fields(self):
        """Заполняет поля данными из загруженного Brand Kit"""
        try:
            brand_kit = self.brand_kit_data['brand_kit']

            self.name_var.set(brand_kit.get('name', ''))
            self.aspect_ratio_var.set(brand_kit.get('aspect_ratio', '16:9'))
            self.randomize_clips_var.set(brand_kit.get('randomize_clips', False))

            self.watermark_path_var.set(brand_kit.get('watermark_path', ''))
            self.watermark_position_var.set(brand_kit.get('watermark_position', 'top_right'))

            self.avatar_path_var.set(brand_kit.get('avatar_clip_path', ''))
            self.avatar_position_var.set(brand_kit.get('avatar_position', 'bottom_left'))
            self.avatar_background_color_var.set(brand_kit.get('avatar_background_color', ''))

            self.cta_path_var.set(brand_kit.get('subscribe_cta_path', ''))
            self.cta_interval_var.set(brand_kit.get('subscribe_cta_interval', 120))

            self.music_path_var.set(brand_kit.get('music_path', ''))
            self.music_volume_var.set(brand_kit.get('music_volume', 20))

            self.lut_path_var.set(brand_kit.get('lut_path', ''))
            self.mask_path_var.set(brand_kit.get('mask_effect_path', ''))
            self.transition_duration_var.set(brand_kit.get('transition_duration', 0.5))

            self.script_var.set(brand_kit.get('script_to_voice_over', ''))

            # Auto intro settings
            auto_intro = self.brand_kit_data.get('auto_intro_settings')
            if auto_intro:
                self.custom_intro_var.set(auto_intro.get('enabled', True))
                self.title_font_var.set(auto_intro.get('title_font', 'Arial'))
                self.title_font_size_var.set(auto_intro.get('title_font_size', 48))
                self.title_font_color_var.set(auto_intro.get('title_font_color', 'FFFFFF'))
                self.bg_type_var.set(auto_intro.get('title_background_type', 'color'))
                self.bg_value_var.set(auto_intro.get('title_background_value', '000000'))

            # Caption settings
            caption = self.brand_kit_data.get('caption_settings')
            if caption:
                self.caption_font_var.set(caption.get('font', 'Arial'))
                self.caption_font_size_var.set(caption.get('font_size', 24))
                self.caption_font_color_var.set(caption.get('font_color', 'FFFFFF'))
                self.caption_stroke_width_var.set(caption.get('stroke_width', 2))
                self.caption_stroke_color_var.set(caption.get('stroke_color', '000000'))
                self.caption_position_var.set(caption.get('position', 'bottom_center'))
                self.caption_max_words_var.set(caption.get('max_words_per_line', 7))

            # Voice settings
            voice = self.brand_kit_data.get('voice_settings')
            if voice:
                self.voice_var.set(voice.get('description', ''))

        except Exception as e:
            self.error_display.show_error(f"Ошибка заполнения полей: {str(e)}")

    def build_basic_tab(self, f):
        # Main settings
        main = ttk.LabelFrame(f, text="Main Settings")
        main.pack(fill='x', padx=16, pady=8)

        ttk.Label(main, text="Name:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        name_entry = ttk.Entry(main, textvariable=self.name_var, width=38)
        name_entry.grid(row=0, column=1, padx=5, pady=6)
        if self.is_edit_mode:
            name_entry.config(state='disabled')  # Не позволяем менять имя при редактировании

        ttk.Label(main, text="Aspect Ratio:").grid(row=0, column=2, sticky='w', padx=5, pady=6)
        ttk.Combobox(main, textvariable=self.aspect_ratio_var, values=["16:9", "9:16"], width=12,
                     state='readonly').grid(row=0, column=3, padx=5, pady=6)

        ttk.Checkbutton(main, text="Randomize Clips Order", variable=self.randomize_clips_var).grid(row=1, column=0,
                                                                                                    columnspan=2,
                                                                                                    sticky='w', padx=5,
                                                                                                    pady=6)

        # Voice
        voice = ttk.LabelFrame(f, text="Voice")
        voice.pack(fill='x', padx=16, pady=8)

        ttk.Label(voice, text="Voice:").grid(row=0, column=0, sticky='w', padx=5, pady=6)

        # Get available voices
        try:
            available_voices = self.brand_kit_service.get_available_voices()
            voice_descriptions = [v['description'] for v in available_voices]
        except Exception as e:
            voice_descriptions = []
            self.error_display.show_error(f"Ошибка загрузки голосов: {str(e)}")

        ttk.Combobox(voice, textvariable=self.voice_var, values=voice_descriptions, width=38, state='readonly').grid(
            row=0, column=1, padx=5, pady=6)

        # Watermark
        watermark = ttk.LabelFrame(f, text="Watermark")
        watermark.pack(fill='x', padx=16, pady=8)

        ttk.Label(watermark, text="File:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(watermark, textvariable=self.watermark_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(watermark, text="Browse...", command=lambda: self.browse_file(self.watermark_path_var)).grid(row=0,
                                                                                                                column=2,
                                                                                                                padx=5,
                                                                                                                pady=6)

        ttk.Label(watermark, text="Position:").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Combobox(watermark, textvariable=self.watermark_position_var, values=[p[0] for p in POSITION_CHOICES],
                     width=20, state='readonly').grid(row=1, column=1, padx=5, pady=6)

        # Avatar
        avatar = ttk.LabelFrame(f, text="Avatar")
        avatar.pack(fill='x', padx=16, pady=8)

        ttk.Label(avatar, text="File:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(avatar, textvariable=self.avatar_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(avatar, text="Browse...", command=lambda: self.browse_file(self.avatar_path_var)).grid(row=0,
                                                                                                          column=2,
                                                                                                          padx=5,
                                                                                                          pady=6)

        ttk.Label(avatar, text="Position:").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Combobox(avatar, textvariable=self.avatar_position_var, values=[p[0] for p in POSITION_CHOICES], width=20,
                     state='readonly').grid(row=1, column=1, padx=5, pady=6)

        ttk.Label(avatar, text="Background Color:").grid(row=2, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(avatar, textvariable=self.avatar_background_color_var, width=20).grid(row=2, column=1, padx=5, pady=6)
        ttk.Label(avatar, text="(6 hex chars, e.g., 00FF00)", font=('Arial', 8)).grid(row=2, column=2, sticky='w',
                                                                                      padx=5, pady=6)

        # CTA
        cta = ttk.LabelFrame(f, text="Subscribe CTA")
        cta.pack(fill='x', padx=16, pady=8)

        ttk.Label(cta, text="File:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(cta, textvariable=self.cta_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(cta, text="Browse...", command=lambda: self.browse_file(self.cta_path_var)).grid(row=0, column=2,
                                                                                                    padx=5, pady=6)

        ttk.Label(cta, text="Interval (sec):").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(cta, textvariable=self.cta_interval_var, width=15).grid(row=1, column=1, padx=5, pady=6)

        # Music
        music = ttk.LabelFrame(f, text="Music")
        music.pack(fill='x', padx=16, pady=8)

        ttk.Label(music, text="File:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(music, textvariable=self.music_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(music, text="Browse...", command=lambda: self.browse_file(self.music_path_var)).grid(row=0, column=2,
                                                                                                        padx=5, pady=6)

        ttk.Label(music, text="Volume (%):").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(music, textvariable=self.music_volume_var, width=15).grid(row=1, column=1, padx=5, pady=6)

    def build_effects_tab(self, f):
        # LUT
        lut = ttk.LabelFrame(f, text="LUT")
        lut.pack(fill='x', padx=16, pady=8)

        ttk.Label(lut, text="LUT File:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(lut, textvariable=self.lut_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(lut, text="Browse...", command=lambda: self.browse_file(self.lut_path_var)).grid(row=0, column=2,
                                                                                                    padx=5, pady=6)

        # Mask
        mask = ttk.LabelFrame(f, text="Mask")
        mask.pack(fill='x', padx=16, pady=8)

        ttk.Label(mask, text="Mask Effect:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(mask, textvariable=self.mask_path_var, width=38).grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(mask, text="Browse...", command=lambda: self.browse_file(self.mask_path_var)).grid(row=0, column=2,
                                                                                                      padx=5, pady=6)

        ttk.Label(mask, text="BG Color:").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        color_frame = ttk.Frame(mask)
        color_frame.grid(row=1, column=1, sticky='w', padx=5, pady=6)
        ttk.Entry(color_frame, textvariable=self.mask_color_var, width=10).pack(side='left')
        ttk.Button(color_frame, text="Pick", command=lambda: self.pick_color(self.mask_color_var), width=5).pack(
            side='left', padx=5)

        # Transitions
        transitions = ttk.LabelFrame(f, text="Transitions")
        transitions.pack(fill='x', padx=16, pady=8)

        ttk.Label(transitions, text="Duration (sec):").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(transitions, textvariable=self.transition_duration_var, width=15).grid(row=0, column=1, padx=5,
                                                                                         pady=6)

        cb_frame = ttk.Frame(transitions)
        cb_frame.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=6)

        cols = 5
        for i, t in enumerate(TRANSITION_TYPE_CHOICES):
            ttk.Checkbutton(cb_frame, text=t, variable=self.transition_vars[t]).grid(row=i // cols, column=i % cols,
                                                                                     sticky='w', padx=3, pady=2)

        # Intro settings
        intro = ttk.LabelFrame(f, text="Intro Settings")
        intro.pack(fill='x', padx=16, pady=8)

        cb = ttk.Checkbutton(intro, text="Custom Intro", variable=self.custom_intro_var, command=self.toggle_intro_fields)
        cb.grid(row=0, column=0, sticky='w', padx=5, pady=6)

        self.intro_file_entry = ttk.Entry(intro, textvariable=self.intro_file_var, width=38)
        self.intro_file_btn = ttk.Button(intro, text="Browse...", command=lambda: self.browse_file(self.intro_file_var))

        ttk.Label(intro, text="Intro File:").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        self.intro_file_entry.grid(row=1, column=1, padx=5, pady=6)
        self.intro_file_btn.grid(row=1, column=2, padx=5, pady=6)

        # Auto intro fields
        self.intro_fields = []
        fields = [
            ("Title Font:", self.title_font_var, CAPTION_FONT_CHOICES),
            ("Font Size:", self.title_font_size_var, None),
            ("Font Color:", self.title_font_color_var, None),
            ("BG Type:", self.bg_type_var, ["color", "image", "video"]),
            ("BG Value:", self.bg_value_var, None),
        ]

        for i, (label, var, vals) in enumerate(fields, start=2):
            ttk.Label(intro, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=6)
            if vals:
                w = ttk.Combobox(intro, textvariable=var, values=vals, width=18, state='readonly')
            else:
                w = ttk.Entry(intro, textvariable=var, width=18)
            w.grid(row=i, column=1, padx=5, pady=6)
            self.intro_fields.append(w)

        self.toggle_intro_fields()

    def toggle_intro_fields(self):
        state = self.custom_intro_var.get()
        if state:
            self.intro_file_entry.config(state='disabled')
            self.intro_file_btn.config(state='disabled')
            for w in self.intro_fields:
                w.config(state='normal')
        else:
            self.intro_file_entry.config(state='normal')
            self.intro_file_btn.config(state='normal')
            for w in self.intro_fields:
                w.config(state='disabled')

    def build_captions_tab(self, f):
        captions = ttk.LabelFrame(f, text="Caption Settings")
        captions.pack(fill='x', padx=16, pady=8)

        ttk.Label(captions, text="Font:").grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Combobox(captions, textvariable=self.caption_font_var, values=CAPTION_FONT_CHOICES, width=18,
                     state='readonly').grid(row=0, column=1, padx=5, pady=6)

        ttk.Label(captions, text="Font Size:").grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(captions, textvariable=self.caption_font_size_var, width=10).grid(row=1, column=1, padx=5, pady=6)

        ttk.Label(captions, text="Font Color:").grid(row=2, column=0, sticky='w', padx=5, pady=6)
        color_frame = ttk.Frame(captions)
        color_frame.grid(row=2, column=1, sticky='w', padx=5, pady=6)
        ttk.Entry(color_frame, textvariable=self.caption_font_color_var, width=10).pack(side='left')
        ttk.Button(color_frame, text="Pick", command=lambda: self.pick_color(self.caption_font_color_var),
                   width=5).pack(side='left', padx=5)

        ttk.Label(captions, text="Stroke Width:").grid(row=3, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(captions, textvariable=self.caption_stroke_width_var, width=10).grid(row=3, column=1, padx=5, pady=6)

        ttk.Label(captions, text="Stroke Color:").grid(row=4, column=0, sticky='w', padx=5, pady=6)
        stroke_color_frame = ttk.Frame(captions)
        stroke_color_frame.grid(row=4, column=1, sticky='w', padx=5, pady=6)
        ttk.Entry(stroke_color_frame, textvariable=self.caption_stroke_color_var, width=10).pack(side='left')
        ttk.Button(stroke_color_frame, text="Pick", command=lambda: self.pick_color(self.caption_stroke_color_var),
                   width=5).pack(side='left', padx=5)

        ttk.Label(captions, text="Position:").grid(row=5, column=0, sticky='w', padx=5, pady=6)
        ttk.Combobox(captions, textvariable=self.caption_position_var, values=[p[0] for p in POSITION_CHOICES],
                     width=18, state='readonly').grid(row=5, column=1, padx=5, pady=6)

        ttk.Label(captions, text="Max Words/Line:").grid(row=6, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(captions, textvariable=self.caption_max_words_var, width=10).grid(row=6, column=1, padx=5, pady=6)

    def build_script_tab(self, f):
        ttk.Label(f, text="Script to Voice Over:").pack(anchor='nw', padx=16, pady=8)

        self.script_text = tk.Text(f, width=80, height=18)
        self.script_text.pack(fill='both', expand=True, padx=16, pady=8)

        # Bind text widget to variable
        self.script_text.bind('<KeyRelease>', self.update_script_var)

        # Set initial text if editing
        if self.brand_kit_data:
            script_content = self.brand_kit_data['brand_kit'].get('script_to_voice_over', '')
            self.script_text.insert('1.0', script_content)

        ttk.Button(f, text="Save BrandKit", command=self.save_brandkit).pack(side='bottom', pady=16)

    def update_script_var(self, event=None):
        self.script_var.set(self.script_text.get('1.0', 'end-1c'))

    def save_brandkit(self):
        try:
            # Подготовка данных для сохранения
            print(self.avatar_background_color_var.get(),)
            brand_kit_data = {
                'name': self.name_var.get(),
                'aspect_ratio': self.aspect_ratio_var.get(),
                'randomize_clips': self.randomize_clips_var.get(),
                'watermark_path': self.watermark_path_var.get() or None,
                'watermark_position': self.watermark_position_var.get(),
                'avatar_clip_path': self.avatar_path_var.get() or None,
                'avatar_position': self.avatar_position_var.get(),
                'avatar_background_color': self.avatar_background_color_var.get(),
                'cta_path': self.cta_path_var.get() or None,
                'cta_interval': self.cta_interval_var.get(),
                'music_path': self.music_path_var.get() or None,
                'music_volume': self.music_volume_var.get(),
                'lut_path': self.lut_path_var.get() or None,
                'mask_effect_path': self.mask_path_var.get() or None,
                'transition_duration': self.transition_duration_var.get(),
                'script_to_voice_over': self.script_text.get('1.0', 'end-1c'),
                'intro_clip_path': self.intro_file_var.get() or None,
            }

            # Найти выбранный голос
            voice_description = self.voice_var.get()
            if voice_description:
                try:
                    voices = self.brand_kit_service.get_available_voices()
                    selected_voice = next((v for v in voices if v['description'] == voice_description), None)
                    if selected_voice:
                        brand_kit_data['voice_id'] = selected_voice['id']
                except Exception as e:
                    self.error_display.show_error(f"Ошибка получения голоса: {str(e)}")

            # Настройки автоматического интро
            brand_kit_data['auto_intro_settings'] = {
                'enabled': self.custom_intro_var.get(),
                'title_font': self.title_font_var.get(),
                'title_font_size': self.title_font_size_var.get(),
                'title_font_color': self.title_font_color_var.get(),
                'title_background_type': self.bg_type_var.get(),
                'title_background_value': self.bg_value_var.get(),
            }

            # Настройки субтитров
            brand_kit_data['caption_settings'] = {
                'font': self.caption_font_var.get(),
                'font_size': self.caption_font_size_var.get(),
                'font_color': self.caption_font_color_var.get(),
                'stroke_width': self.caption_stroke_width_var.get(),
                'stroke_color': self.caption_stroke_color_var.get(),
                'position': self.caption_position_var.get(),
                'max_words_per_line': self.caption_max_words_var.get(),
            }

            # Получить ID выбранных переходов
            try:
                available_transitions = self.brand_kit_service.get_available_transitions()
                selected_transition_ids = []
                for transition_name, var in self.transition_vars.items():
                    if var.get():
                        transition = next((t for t in available_transitions if t['name'] == transition_name), None)
                        if transition:
                            selected_transition_ids.append(transition['id'])
                brand_kit_data['transition_ids'] = selected_transition_ids
            except Exception as e:
                self.error_display.show_error(f"Ошибка получения переходов: {str(e)}")
                brand_kit_data['transition_ids'] = []

            # Валидация
            if not brand_kit_data['name'].strip():
                self.error_display.show_error("Имя Brand Kit не может быть пустым")
                return

            # Сохранение или обновление
            if self.is_edit_mode:
                success = self.brand_kit_service.update_brand_kit(self.brand_kit_name, {
                    'brand_kit': brand_kit_data,
                    'auto_intro_settings': brand_kit_data['auto_intro_settings'],
                    'caption_settings': brand_kit_data['caption_settings'],
                    'transition_ids': brand_kit_data['transition_ids']
                })
                if success:
                    messagebox.showinfo("Успех", "Brand Kit успешно обновлен!")
                    self.destroy()
                else:
                    self.error_display.show_error("Не удалось обновить Brand Kit")
            else:
                result = self.brand_kit_service.create_brand_kit(brand_kit_data)
                if result:
                    messagebox.showinfo("Успех", "Brand Kit успешно создан!")
                    self.destroy()
                else:
                    self.error_display.show_error("Не удалось создать Brand Kit")

        except Exception as e:
            self.error_display.show_error(f"Ошибка сохранения: {str(e)}")

    def browse_file(self, var):
        filename = filedialog.askopenfilename()
        if filename:
            var.set(filename)

    def pick_color(self, var):
        color = colorchooser.askcolor(title="Choose Color")
        if color and color[1]:
            var.set(color[1].lstrip('#'))


# --- Main Application ---
class VideoEditorMaxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Editor Max")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Initialize services
        try:
            self.brand_kit_service = BrandKitService()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось инициализировать BrandKitService: {str(e)}")
            self.root.destroy()
            return

        self.api_keys = API_KEYS
        self.jobs = JOBS

        # Error display
        self.error_display = ErrorDisplay(self.root)

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(side='top', fill='x', pady=5)

        ttk.Label(header, text="Video Editor Max", font=("Arial", 20, "bold")).pack(side='left', padx=20)

        gear_btn = ttk.Button(header, text="⚙", width=3, command=self.show_menu)
        gear_btn.pack(side='right', padx=20)

        # Body
        self.body = ttk.Frame(self.root)
        self.body.pack(fill='both', expand=True, padx=20, pady=10)

        # Footer
        footer = ttk.Frame(self.root)
        footer.pack(side='bottom', fill='x', pady=10)

        ttk.Label(footer, text="Jobs:").pack(side='left', padx=10)

        jobs_frame = ttk.Frame(footer)
        jobs_frame.pack(side='left', fill='x', expand=True, padx=10, pady=5)

        self.jobs_tree = ttk.Treeview(jobs_frame, columns=("title", "status", "progress"), show="headings", height=2)
        self.jobs_tree.heading("title", text="Video")
        self.jobs_tree.heading("status", text="Status")
        self.jobs_tree.heading("progress", text="Progress")
        self.jobs_tree.pack(side='left', fill='x', expand=True)

        jobs_scrollbar = ttk.Scrollbar(jobs_frame, orient="vertical", command=self.jobs_tree.yview)
        self.jobs_tree.configure(yscrollcommand=jobs_scrollbar.set)
        jobs_scrollbar.pack(side='right', fill='y')

        self.refresh_jobs()

        ttk.Button(footer, text="Create New Videos", command=self.create_new_video).pack(side='right', padx=20, pady=5)

        # Show default page
        self.show_brandkit_page()

    def refresh_jobs(self):
        for i in self.jobs_tree.get_children():
            self.jobs_tree.delete(i)
        for job in self.jobs:
            self.jobs_tree.insert('', 'end', values=(job['title'], job['status'], f"{job['progress']}%"))

    def show_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="BrandKit", command=self.show_brandkit_page)
        menu.add_command(label="API Keys", command=self.show_apikeys_page)
        menu.add_command(label="Voices", command=self.show_voices_page)

        x = self.root.winfo_rootx() + self.root.winfo_width() - 50
        y = self.root.winfo_rooty() + 50
        menu.post(x, y)

    def show_brandkit_page(self):
        self._clear_body()

        frame = ttk.Frame(self.body)
        frame.pack(fill='both', expand=True)

        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=10)

        ttk.Label(title_frame, text="Brand Kits", font=("Arial", 16, "bold")).pack(anchor='w')
        ttk.Label(title_frame, text="Manage your brand kits for video creation").pack(anchor='w')

        # Load brand kits from database
        try:
            brand_kit_names = self.brand_kit_service.get_brand_kit_names()
            brand_kits_data = []

            for name in brand_kit_names:
                try:
                    kit_data = self.brand_kit_service.load_brand_kit(name, use_cache=False)
                    if kit_data:
                        brand_kit = kit_data['brand_kit']
                        brand_kits_data.append({
                            'name': brand_kit['name'],
                            'aspect_ratio': brand_kit.get('aspect_ratio', '16:9'),
                            'created_at': brand_kit.get('created_at', 'Unknown')[:10] if brand_kit.get(
                                'created_at') else 'Unknown'
                        })
                except Exception as e:
                    self.error_display.show_error(f"Ошибка загрузки Brand Kit '{name}': {str(e)}")

        except Exception as e:
            brand_kits_data = []
            self.error_display.show_error(f"Ошибка загрузки Brand Kits: {str(e)}")

        columns = ["name", "aspect_ratio", "created_at"]
        actions = ["Clone", "Edit", "Delete"]

        self.brandkit_table = SimpleTable(frame, columns, brand_kits_data, actions,
                                          [self.clone_brandkit, self.edit_brandkit, self.delete_brandkit])
        self.brandkit_table.pack(fill='both', expand=True, padx=10, pady=10)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill='x', pady=10)

        ttk.Button(action_frame, text="Create New Brand Kit", command=self.open_brandkit_window).pack()

    def clone_brandkit(self, idx):
        try:
            brand_kit_name = self.brandkit_table.data[idx]['name']

            # Загружаем данные оригинального Brand Kit
            original_data = self.brand_kit_service.load_brand_kit(brand_kit_name)
            if not original_data:
                self.error_display.show_error(f"Не удалось загрузить Brand Kit '{brand_kit_name}' для клонирования")
                return

            # Создаем новое имя
            clone_name = f"{brand_kit_name} (Copy)"
            counter = 1
            while clone_name in self.brand_kit_service.get_brand_kit_names():
                counter += 1
                clone_name = f"{brand_kit_name} (Copy {counter})"

            # Подготавливаем данные для клонирования
            clone_data = original_data['brand_kit'].copy()
            clone_data['name'] = clone_name

            # Добавляем связанные настройки
            if original_data.get('auto_intro_settings'):
                clone_data['auto_intro_settings'] = original_data['auto_intro_settings']
            if original_data.get('caption_settings'):
                clone_data['caption_settings'] = original_data['caption_settings']

            # Получаем ID переходов
            transition_ids = []
            if original_data.get('transitions'):
                for transition in original_data['transitions']:
                    transition_ids.append(transition['id'])
            clone_data['transition_ids'] = transition_ids

            # Получаем ID голоса
            if original_data.get('voice_settings'):
                clone_data['voice_id'] = original_data['voice_settings']['id']

            # Создаем клон
            result = self.brand_kit_service.create_brand_kit(clone_data)
            if result:
                messagebox.showinfo("Успех", f"Brand Kit '{clone_name}' успешно создан!")
                self.show_brandkit_page()  # Обновляем список
            else:
                self.error_display.show_error("Не удалось создать клон Brand Kit")

        except Exception as e:
            self.error_display.show_error(f"Ошибка клонирования Brand Kit: {str(e)}")

    def edit_brandkit(self, idx):
        try:
            brand_kit_name = self.brandkit_table.data[idx]['name']
            BrandKitEditor(self.root, self.brand_kit_service, brand_kit_name)
        except Exception as e:
            self.error_display.show_error(f"Ошибка открытия редактора: {str(e)}")

    def delete_brandkit(self, idx):
        try:
            brand_kit_name = self.brandkit_table.data[idx]['name']
            if messagebox.askyesno("Подтверждение", f"Удалить Brand Kit '{brand_kit_name}'?"):
                success = self.brand_kit_service.delete_brand_kit(brand_kit_name)
                if success:
                    messagebox.showinfo("Успех", f"Brand Kit '{brand_kit_name}' удален!")
                    self.show_brandkit_page()  # Обновляем список
                else:
                    self.error_display.show_error(f"Не удалось удалить Brand Kit '{brand_kit_name}'")
        except Exception as e:
            self.error_display.show_error(f"Ошибка удаления Brand Kit: {str(e)}")

    def open_brandkit_window(self):
        try:
            BrandKitEditor(self.root, self.brand_kit_service)
        except Exception as e:
            self.error_display.show_error(f"Ошибка открытия редактора: {str(e)}")

    def show_apikeys_page(self):
        self._clear_body()

        frame = ttk.Frame(self.body)
        frame.pack(fill='both', expand=True)

        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=10)

        ttk.Label(title_frame, text="API Keys", font=("Arial", 16, "bold")).pack(anchor='w')
        ttk.Label(title_frame, text="Manage your API keys for voice services").pack(anchor='w')

        columns = ["service", "key", "active"]
        actions = ["Delete"]

        self.apikey_table = SimpleTable(frame, columns, self.api_keys, actions, [self.delete_apikey])
        self.apikey_table.pack(fill='both', expand=True, padx=10, pady=10)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill='x', pady=10)

        ttk.Button(action_frame, text="Add New API Key", command=self.open_add_apikey_window).pack()

    def delete_apikey(self, idx):
        if messagebox.askyesno("Подтверждение", f"Удалить API Key '{self.api_keys[idx]['service']}'?"):
            del self.api_keys[idx]
            self.apikey_table.refresh(self.api_keys)

    def show_voices_page(self):
        self._clear_body()

        frame = ttk.Frame(self.body)
        frame.pack(fill='both', expand=True)

        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=10)

        ttk.Label(title_frame, text="Voices", font=("Arial", 16, "bold")).pack(anchor='w')
        ttk.Label(title_frame, text="Manage voice profiles for text-to-speech").pack(anchor='w')

        # Load voices from database
        try:
            voices_data = self.brand_kit_service.get_available_voices()
        except Exception as e:
            voices_data = []
            self.error_display.show_error(f"Ошибка загрузки голосов: {str(e)}")

        columns = ["provider", "language_code", "voice_id", "description", "speed"]
        actions = ["Delete"]

        self.voice_table = SimpleTable(frame, columns, voices_data, actions, [self.delete_voice])
        self.voice_table.pack(fill='both', expand=True, padx=10, pady=10)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill='x', pady=10)

        ttk.Button(action_frame, text="Add New Voice", command=self.open_add_voice_window).pack()

    def delete_voice(self, idx):
        if messagebox.askyesno("Подтверждение", f"Удалить голос '{self.voice_table.data[idx]['description']}'?"):
            # Здесь нужно будет добавить метод удаления голоса в BrandKitService
            messagebox.showinfo("Информация", "Функция удаления голосов пока не реализована в BrandKitService")

    def open_add_voice_window(self):
        # Здесь нужно будет добавить метод создания голоса в BrandKitService
        messagebox.showinfo("Информация", "Функция добавления голосов пока не реализована в BrandKitService")

    def open_add_apikey_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add New API Key")
        win.geometry("350x180")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=20)
        frame.pack(fill='both', expand=True)

        service_var = tk.StringVar()
        key_var = tk.StringVar()
        active_var = tk.BooleanVar(value=True)

        ttk.Label(frame, text="Service:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Combobox(frame, textvariable=service_var, values=[p[0] for p in TTS_PROVIDER_CHOICES],
                     state='readonly').grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="API Key:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=key_var, show="*").grid(row=1, column=1, padx=5, pady=5)

        ttk.Checkbutton(frame, text="Active", variable=active_var).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        ttk.Button(frame, text="Save", command=lambda: self.save_apikey(win, service_var, key_var, active_var)).grid(
            row=3, column=0, columnspan=2, pady=15)

    def save_apikey(self, win, service_var, key_var, active_var):
        self.api_keys.append({
            'service': service_var.get(),
            'key': key_var.get(),
            'active': active_var.get()
        })
        messagebox.showinfo("Успех", "API ключ успешно добавлен")
        win.destroy()
        self.apikey_table.refresh(self.api_keys)

    def create_new_video(self):
        messagebox.showinfo("Создание видео", "Мастер создания видео (не реализован в этой демо-версии)")

    def _clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()
        self.error_display.hide()

