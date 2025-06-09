from typing import Optional, Dict, Any, List
from models import (
    BrandKit, AutoIntroSetting, Caption, Voice, Transition,
    BrandKitTransition, register_models
)


class BrandKitLoader:
    """Класс для загрузки Brand Kit со всеми связанными данными"""

    @staticmethod
    def load_brand_kit_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        Загружает Brand Kit по имени со всеми связанными объектами

        Args:
            name: Имя Brand Kit для загрузки

        Returns:
            Словарь с данными Brand Kit или None если не найден
        """
        try:
            # # Подключаемся к базе данных
            # db.connect(reuse_if_open=True)

            # Загружаем основной Brand Kit
            brand_kit = BrandKit.get(BrandKit.name == name)

            # Загружаем связанные объекты
            result = {
                'brand_kit': brand_kit,
                'auto_intro_settings': BrandKitLoader._load_auto_intro_settings(brand_kit),
                'caption_settings': BrandKitLoader._load_caption_settings(brand_kit),
                'voice_settings': BrandKitLoader._load_voice_settings(brand_kit),
                'transitions': BrandKitLoader._load_transitions(brand_kit)
            }

            return result

        except BrandKit.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка при загрузке Brand Kit '{name}': {e}")
            return None

    @staticmethod
    def load_brand_kit_by_id(brand_kit_id: int) -> Optional[Dict[str, Any]]:
        """
        Загружает Brand Kit по ID со всеми связанными объектами

        Args:
            brand_kit_id: ID Brand Kit для загрузки

        Returns:
            Словарь с данными Brand Kit или None если не найден
        """
        try:
            # db.connect(reuse_if_open=True)

            brand_kit = BrandKit.get_by_id(brand_kit_id)

            result = {
                'brand_kit': brand_kit,
                'auto_intro_settings': BrandKitLoader._load_auto_intro_settings(brand_kit),
                'caption_settings': BrandKitLoader._load_caption_settings(brand_kit),
                'voice_settings': BrandKitLoader._load_voice_settings(brand_kit),
                'transitions': BrandKitLoader._load_transitions(brand_kit)
            }

            return result

        except BrandKit.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка при загрузке Brand Kit с ID {brand_kit_id}: {e}")
            return None

    @staticmethod
    def _load_auto_intro_settings(brand_kit: BrandKit) -> Optional[AutoIntroSetting]:
        """Загружает настройки автоматического интро"""
        try:
            return AutoIntroSetting.get(AutoIntroSetting.brand_kit == brand_kit)
        except AutoIntroSetting.DoesNotExist:
            return None

    @staticmethod
    def _load_caption_settings(brand_kit: BrandKit) -> Optional[Caption]:
        """Загружает настройки субтитров"""
        try:
            return Caption.get(Caption.brand_kit == brand_kit)
        except Caption.DoesNotExist:
            return None

    @staticmethod
    def _load_voice_settings(brand_kit: BrandKit) -> Optional[Voice]:
        """Загружает настройки голоса"""
        return brand_kit.voice if brand_kit.voice else None

    @staticmethod
    def _load_transitions(brand_kit: BrandKit) -> List[Transition]:
        """Загружает список переходов для Brand Kit"""
        try:
            transitions = (Transition
                           .select()
                           .join(BrandKitTransition)
                           .where(BrandKitTransition.brand_kit == brand_kit))
            return list(transitions)
        except Exception:
            return []

    @staticmethod
    def load_all_brand_kits() -> List[Dict[str, Any]]:
        """
        Загружает все Brand Kit со всеми связанными объектами

        Returns:
            Список словарей с данными всех Brand Kit
        """
        try:
            # db.connect(reuse_if_open=True)

            brand_kits = BrandKit.select()
            result = []

            for brand_kit in brand_kits:
                kit_data = {
                    'brand_kit': brand_kit,
                    'auto_intro_settings': BrandKitLoader._load_auto_intro_settings(brand_kit),
                    'caption_settings': BrandKitLoader._load_caption_settings(brand_kit),
                    'voice_settings': BrandKitLoader._load_voice_settings(brand_kit),
                    'transitions': BrandKitLoader._load_transitions(brand_kit)
                }
                result.append(kit_data)

            return result

        except Exception as e:
            print(f"Ошибка при загрузке всех Brand Kit: {e}")
            return []

    @staticmethod
    def get_brand_kit_names() -> List[str]:
        """
        Возвращает список имен всех Brand Kit

        Returns:
            Список имен Brand Kit
        """
        try:
            # db.connect(reuse_if_open=True)
            brand_kits = BrandKit.select(BrandKit.name)
            return [kit.name for kit in brand_kits]
        except Exception as e:
            print(f"Ошибка при получении имен Brand Kit: {e}")
            return []


# Дополнительные утилиты для работы с Brand Kit
class BrandKitUtils:
    """Утилиты для работы с Brand Kit"""

    @staticmethod
    def create_default_brand_kit(name: str = "Default") -> Optional[BrandKit]:
        """
        Создает Brand Kit по умолчанию с базовыми настройками

        Args:
            name: Имя для нового Brand Kit

        Returns:
            Созданный Brand Kit или None при ошибке
        """
        try:
            # db.connect(reuse_if_open=True)

            # Создаем Brand Kit
            brand_kit = BrandKit.create(
                name=name,
                randomize_clips=False,
                watermark_position="top_right",
                avatar_position="bottom_left",
                subscribe_cta_interval=120,
                aspect_ratio="16:9",
                music_volume=20,
                transition_duration=0.5,
                script_to_voice_over=""
            )

            # Создаем связанные объекты автоматически через ensure_related_objects
            brand_kit.ensure_related_objects()

            return brand_kit

        except Exception as e:
            print(f"Ошибка при создании Brand Kit по умолчанию: {e}")
            return None

    @staticmethod
    def duplicate_brand_kit(source_name: str, new_name: str) -> Optional[BrandKit]:
        """
        Дублирует существующий Brand Kit с новым именем

        Args:
            source_name: Имя исходного Brand Kit
            new_name: Имя для нового Brand Kit

        Returns:
            Новый Brand Kit или None при ошибке
        """
        try:
            # Загружаем исходный Brand Kit
            source_data = BrandKitLoader.load_brand_kit_by_name(source_name)
            if not source_data:
                return None

            source_kit = source_data['brand_kit']

            # Создаем новый Brand Kit с теми же настройками
            new_kit = BrandKit.create(
                name=new_name,
                intro_clip_path=source_kit.intro_clip_path,
                randomize_clips=source_kit.randomize_clips,
                watermark_path=source_kit.watermark_path,
                watermark_position=source_kit.watermark_position,
                avatar_clip_path=source_kit.avatar_clip_path,
                avatar_position=source_kit.avatar_position,
                subscribe_cta_path=source_kit.subscribe_cta_path,
                subscribe_cta_interval=source_kit.subscribe_cta_interval,
                voice=source_kit.voice,
                aspect_ratio=source_kit.aspect_ratio,
                music_path=source_kit.music_path,
                music_volume=source_kit.music_volume,
                lut_path=source_kit.lut_path,
                mask_effect_path=source_kit.mask_effect_path,
                transition_duration=source_kit.transition_duration,
                script_to_voice_over=source_kit.script_to_voice_over
            )

            # Копируем настройки автоматического интро
            if source_data['auto_intro_settings']:
                auto_intro = source_data['auto_intro_settings']
                AutoIntroSetting.create(
                    brand_kit=new_kit,
                    enabled=auto_intro.enabled,
                    title_font=auto_intro.title_font,
                    title_font_size=auto_intro.title_font_size,
                    title_font_color=auto_intro.title_font_color,
                    title_background_type=auto_intro.title_background_type,
                    title_background_value=auto_intro.title_background_value,
                    typewriter_speed=auto_intro.typewriter_speed
                )

            # Копируем настройки субтитров
            if source_data['caption_settings']:
                caption = source_data['caption_settings']
                Caption.create(
                    brand_kit=new_kit,
                    font=caption.font,
                    font_size=caption.font_size,
                    font_color=caption.font_color,
                    stroke_width=caption.stroke_width,
                    stroke_color=caption.stroke_color,
                    position=caption.position,
                    max_words_per_line=caption.max_words_per_line
                )

            # Копируем переходы
            for transition in source_data['transitions']:
                BrandKitTransition.create(
                    brand_kit=new_kit,
                    transition=transition
                )

            return new_kit

        except Exception as e:
            print(f"Ошибка при дублировании Brand Kit: {e}")
            return None


# Пример использования
def example_usage():
    """Пример использования функций загрузки Brand Kit"""

    # Загрузка Brand Kit по имени
    kit_data = BrandKitLoader.load_brand_kit_by_name("Default")
    if kit_data:
        brand_kit = kit_data['brand_kit']
        print(f"Загружен Brand Kit: {brand_kit.name}")
        print(f"Соотношение сторон: {brand_kit.aspect_ratio}")
        print(f"Громкость музыки: {brand_kit.music_volume}%")

        # Проверяем настройки субтитров
        if kit_data['caption_settings']:
            caption = kit_data['caption_settings']
            print(f"Шрифт субтитров: {caption.font}")
            print(f"Размер шрифта: {caption.font_size}")

    # Получение списка всех Brand Kit
    all_names = BrandKitLoader.get_brand_kit_names()
    print(f"Доступные Brand Kit: {all_names}")

    # Создание Brand Kit по умолчанию
    default_kit = BrandKitUtils.create_default_brand_kit("My Default Kit")
    if default_kit:
        print(f"Создан новый Brand Kit: {default_kit.name}")


if __name__ == "__main__":
    register_models()
    example_usage()
