# services/brand_kit_service.py
from typing import Optional, Dict, Any, List
import os
from database.models import (
    BrandKit, AutoIntroSetting, Caption, Voice, Transition,
    BrandKitTransition, db
)


class BrandKitService:
    """Комплексный сервис для управления Brand Kit"""

    def __init__(self):
        self._cache = {}
        self._ensure_db_connection()

    def _ensure_db_connection(self):
        """Обеспечивает подключение к базе данных"""
        if not db.is_connection_usable():
            db.connect(reuse_if_open=True)

    def create_brand_kit(self, brand_kit_data: Dict[str, Any]) -> Optional[BrandKit]:
        """
        Создает новый Brand Kit со всеми связанными объектами

        Args:
            brand_kit_data: Словарь с данными Brand Kit

        Returns:
            Созданный Brand Kit или None при ошибке
        """
        try:
            # Валидация обязательных полей
            if not brand_kit_data.get('name'):
                raise ValueError("Имя Brand Kit обязательно")

            # Проверка уникальности имени
            if BrandKit.select().where(BrandKit.name == brand_kit_data['name']).exists():
                raise ValueError(f"Brand Kit с именем '{brand_kit_data['name']}' уже существует")

            # Получение голоса если указан
            voice = None
            if brand_kit_data.get('voice_id'):
                try:
                    voice = Voice.get_by_id(brand_kit_data['voice_id'])
                except Voice.DoesNotExist:
                    print(f"Голос с ID {brand_kit_data['voice_id']} не найден")

            # Создание основного Brand Kit
            brand_kit = BrandKit.create(
                name=brand_kit_data['name'],
                intro_clip_path=brand_kit_data.get('intro_clip_path'),
                randomize_clips=brand_kit_data.get('randomize_clips', False),
                watermark_path=brand_kit_data.get('watermark_path'),
                watermark_position=brand_kit_data.get('watermark_position', 'top_right'),
                avatar_clip_path=brand_kit_data.get('avatar_clip_path'),
                avatar_position=brand_kit_data.get('avatar_position', 'bottom_left'),
                avatar_background_color=brand_kit_data.get('avatar_background_color'),
                cta_path=brand_kit_data.get('cta_path'),
                cta_interval=brand_kit_data.get('cta_interval', 120),
                voice=voice,
                aspect_ratio=brand_kit_data.get('aspect_ratio', '16:9'),
                music_path=brand_kit_data.get('music_path'),
                music_volume=brand_kit_data.get('music_volume', 20),
                lut_path=brand_kit_data.get('lut_path'),
                mask_effect_path=brand_kit_data.get('mask_effect_path'),
                transition_duration=brand_kit_data.get('transition_duration', 0.5),
                script_to_voice_over=brand_kit_data.get('script_to_voice_over', '')
            )

            # Создание настроек автоматического интро
            auto_intro_data = brand_kit_data.get('auto_intro_settings', {})
            AutoIntroSetting.create(
                brand_kit=brand_kit,
                enabled=auto_intro_data.get('enabled', True),
                title_font=auto_intro_data.get('title_font', 'Arial'),
                title_font_size=auto_intro_data.get('title_font_size', 48),
                title_font_color=auto_intro_data.get('title_font_color', 'FFFFFF'),
                title_background_type=auto_intro_data.get('title_background_type', 'color'),
                title_background_value=auto_intro_data.get('title_background_value', '000000')
            )

            # Создание настроек субтитров
            caption_data = brand_kit_data.get('caption_settings', {})
            Caption.create(
                brand_kit=brand_kit,
                font=caption_data.get('font', 'Arial'),
                font_size=caption_data.get('font_size', 24),
                font_color=caption_data.get('font_color', 'FFFFFF'),
                stroke_width=caption_data.get('stroke_width', 2),
                stroke_color=caption_data.get('stroke_color', '000000'),
                position=caption_data.get('position', 'bottom_center'),
                max_words_per_line=caption_data.get('max_words_per_line', 7)
            )

            # Добавление переходов
            transition_ids = brand_kit_data.get('transition_ids', [])
            for transition_id in transition_ids:
                try:
                    transition = Transition.get_by_id(transition_id)
                    BrandKitTransition.create(
                        brand_kit=brand_kit,
                        transition=transition
                    )
                except Transition.DoesNotExist:
                    print(f"Переход с ID {transition_id} не найден")

            # Очистка кэша
            self._cache.clear()

            return brand_kit

        except Exception as e:
            print(f"Ошибка создания Brand Kit: {e}")
            return None

    def load_brand_kit(self, name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Загружает Brand Kit со всеми связанными данными

        Args:
            name: Имя Brand Kit
            use_cache: Использовать кэширование

        Returns:
            Словарь с данными Brand Kit или None
        """
        if use_cache and name in self._cache:
            return self._cache[name]

        try:
            # Загрузка основного Brand Kit
            brand_kit = BrandKit.get(BrandKit.name == name)

            # Загрузка связанных объектов
            result = {
                'brand_kit': self._serialize_brand_kit(brand_kit),
                'auto_intro_settings': self._load_auto_intro_settings(brand_kit),
                'caption_settings': self._load_caption_settings(brand_kit),
                'voice_settings': self._load_voice_settings(brand_kit),
                'transitions': self._load_transitions(brand_kit),
                'files_info': self._get_files_info(brand_kit)
            }

            if use_cache:
                self._cache[name] = result

            return result

        except BrandKit.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка загрузки Brand Kit '{name}': {e}")
            return None

    def _serialize_brand_kit(self, brand_kit: BrandKit) -> Dict[str, Any]:
        """Сериализует Brand Kit в словарь"""
        return {
            'id': brand_kit.id,
            'name': brand_kit.name,
            'intro_clip_path': brand_kit.intro_clip_path,
            'randomize_clips': brand_kit.randomize_clips,
            'watermark_path': brand_kit.watermark_path,
            'watermark_position': brand_kit.watermark_position,
            'avatar_clip_path': brand_kit.avatar_clip_path,
            'avatar_position': brand_kit.avatar_position,
            'avatar_background_color': brand_kit.avatar_background_color,
            'cta_path': brand_kit.cta_path,
            'cta_interval': brand_kit.cta_interval,
            'aspect_ratio': brand_kit.aspect_ratio,
            'music_path': brand_kit.music_path,
            'music_volume': brand_kit.music_volume,
            'lut_path': brand_kit.lut_path,
            'mask_effect_path': brand_kit.mask_effect_path,
            'transition_duration': brand_kit.transition_duration,
            'script_to_voice_over': brand_kit.script_to_voice_over,
            'created_at': brand_kit.created_at.isoformat() if brand_kit.created_at else None,
            'updated_at': brand_kit.updated_at.isoformat() if brand_kit.updated_at else None
        }

    def _load_auto_intro_settings(self, brand_kit: BrandKit) -> Optional[Dict[str, Any]]:
        """Загружает настройки автоматического интро"""
        try:
            auto_intro = AutoIntroSetting.get(AutoIntroSetting.brand_kit == brand_kit)
            return {
                'enabled': auto_intro.enabled,
                'title_font': auto_intro.title_font,
                'title_font_size': auto_intro.title_font_size,
                'title_font_color': auto_intro.title_font_color,
                'title_background_type': auto_intro.title_background_type,
                'title_background_value': auto_intro.title_background_value
            }
        except AutoIntroSetting.DoesNotExist:
            return None

    def _load_caption_settings(self, brand_kit: BrandKit) -> Optional[Dict[str, Any]]:
        """Загружает настройки субтитров"""
        try:
            caption = Caption.get(Caption.brand_kit == brand_kit)
            return {
                'font': caption.font,
                'font_size': caption.font_size,
                'font_color': caption.font_color,
                'stroke_width': caption.stroke_width,
                'stroke_color': caption.stroke_color,
                'position': caption.position,
                'max_words_per_line': caption.max_words_per_line
            }
        except Caption.DoesNotExist:
            return None

    def _load_voice_settings(self, brand_kit: BrandKit) -> Optional[Dict[str, Any]]:
        """Загружает настройки голоса"""
        if brand_kit.voice:
            return {
                'id': brand_kit.voice.id,
                'provider': brand_kit.voice.provider,
                'language_code': brand_kit.language_code,
                'voice_id': brand_kit.voice.voice_id,
                'group_id': brand_kit.voice.group_id,
                'description': brand_kit.voice.description,
                'speed': brand_kit.voice.speed
            }
        return None

    def _load_transitions(self, brand_kit: BrandKit) -> List[Dict[str, Any]]:
        """Загружает список переходов"""
        try:
            transitions = (Transition
                           .select()
                           .join(BrandKitTransition)
                           .where(BrandKitTransition.brand_kit == brand_kit))

            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'description': t.description
                }
                for t in transitions
            ]
        except Exception:
            return []

    def _get_files_info(self, brand_kit: BrandKit) -> Dict[str, Dict[str, Any]]:
        """Получает информацию о файлах Brand Kit"""
        files_info = {}

        file_paths = {
            'intro_clip': brand_kit.intro_clip_path,
            'watermark': brand_kit.watermark_path,
            'avatar_clip': brand_kit.avatar_clip_path,
            'cta': brand_kit.cta_path,
            'music': brand_kit.music_path,
            'lut': brand_kit.lut_path,
            'mask_effect': brand_kit.mask_effect_path
        }

        for file_type, file_path in file_paths.items():
            if file_path:
                files_info[file_type] = {
                    'path': file_path,
                    'exists': os.path.exists(file_path),
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }

        return files_info

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных голосов"""
        try:
            voices = Voice.select()
            return [
                {
                    'id': voice.id,
                    'description': voice.description
                }
                for voice in voices
            ]
        except Exception as e:
            print(f"Ошибка получения голосов: {e}")
            return []

    def get_available_transitions(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных переходов"""
        try:
            transitions = Transition.select()
            return [
                {
                    'id': transition.id,
                    'name': transition.name,
                    'description': transition.description
                }
                for transition in transitions
            ]
        except Exception as e:
            print(f"Ошибка получения переходов: {e}")
            return []

    def get_brand_kit_names(self) -> List[str]:
        """Возвращает список имен всех Brand Kit"""
        try:
            brand_kits = BrandKit.select(BrandKit.name)
            return [kit.name for kit in brand_kits]
        except Exception as e:
            print(f"Ошибка получения имен Brand Kit: {e}")
            return []

    def update_brand_kit(self, name: str, updates: Dict[str, Any]) -> bool:
        """Обновляет существующий Brand Kit"""
        try:
            brand_kit = BrandKit.get(BrandKit.name == name)

            # Обновление основных полей
            for field, value in updates.get('brand_kit', {}).items():
                if hasattr(brand_kit, field):
                    setattr(brand_kit, field, value)

            brand_kit.save()

            # Обновление связанных объектов
            if 'auto_intro_settings' in updates:
                self._update_auto_intro_settings(brand_kit, updates['auto_intro_settings'])

            if 'caption_settings' in updates:
                self._update_caption_settings(brand_kit, updates['caption_settings'])

            if 'transition_ids' in updates:
                self._update_transitions(brand_kit, updates['transition_ids'])

            # Очистка кэша
            if name in self._cache:
                del self._cache[name]

            return True

        except Exception as e:
            print(f"Ошибка обновления Brand Kit '{name}': {e}")
            return False

    def _update_auto_intro_settings(self, brand_kit: BrandKit, settings: Dict[str, Any]):
        """Обновляет настройки автоматического интро"""
        try:
            auto_intro = AutoIntroSetting.get(AutoIntroSetting.brand_kit == brand_kit)
            for field, value in settings.items():
                if hasattr(auto_intro, field):
                    setattr(auto_intro, field, value)
            auto_intro.save()
        except AutoIntroSetting.DoesNotExist:
            AutoIntroSetting.create(brand_kit=brand_kit, **settings)

    def _update_caption_settings(self, brand_kit: BrandKit, settings: Dict[str, Any]):
        """Обновляет настройки субтитров"""
        try:
            caption = Caption.get(Caption.brand_kit == brand_kit)
            for field, value in settings.items():
                if hasattr(caption, field):
                    setattr(caption, field, value)
            caption.save()
        except Caption.DoesNotExist:
            Caption.create(brand_kit=brand_kit, **settings)

    def _update_transitions(self, brand_kit: BrandKit, transition_ids: List[int]):
        """Обновляет переходы Brand Kit"""
        # Удаляем старые связи
        BrandKitTransition.delete().where(BrandKitTransition.brand_kit == brand_kit).execute()

        # Добавляем новые связи
        for transition_id in transition_ids:
            try:
                transition = Transition.get_by_id(transition_id)
                BrandKitTransition.create(brand_kit=brand_kit, transition=transition)
            except Transition.DoesNotExist:
                print(f"Переход с ID {transition_id} не найден")

    def delete_brand_kit(self, name: str) -> bool:
        """Удаляет Brand Kit и все связанные данные"""
        try:
            brand_kit = BrandKit.get(BrandKit.name == name)
            brand_kit.delete_instance(recursive=True)

            # Очистка кэша
            if name in self._cache:
                del self._cache[name]

            return True

        except BrandKit.DoesNotExist:
            return False
        except Exception as e:
            print(f"Ошибка удаления Brand Kit '{name}': {e}")
            return False
