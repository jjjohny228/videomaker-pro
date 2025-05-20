import os
from typing import List, Dict, Any
import math


def format_time(seconds: float) -> str:
    """Форматирует время в формат ASS (H:MM:SS.cc)"""
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    centisecs = int((seconds * 100) % 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def generate_ass_subtitles(sentences: List[str], output_file: str, video_duration: float,
                           font: str = "Arial", font_size: int = 24, color: str = "&HFFFFFF",
                           stroke_width: int = 2, stroke_color: str = "&H000000",
                           alignment: int = 2, max_words_per_line: int = 7) -> str:
    """
    Генерирует файл субтитров ASS

    Args:
        sentences: Список предложений
        output_file: Путь к выходному файлу
        video_duration: Длительность видео в секундах
        font: Шрифт
        font_size: Размер шрифта
        color: Цвет текста в формате ASS (&HRRGGBB)
        stroke_width: Толщина обводки
        stroke_color: Цвет обводки в формате ASS (&HRRGGBB)
        alignment: Позиция (1-9, как на цифровой клавиатуре)
        max_words_per_line: Максимальное количество слов в строке

    Returns:
        Путь к созданному файлу субтитров
    """
    # Создаем заголовок ASS файла
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{color},&H00FFFFFF,{stroke_color},&H00000000,0,0,0,0,100,100,0,0,1,{stroke_width},0,{alignment},20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
        font=font,
        font_size=font_size,
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        alignment=alignment
    )

    # Распределяем время для каждого предложения
    total_chars = sum(len(s) for s in sentences)
    char_duration = video_duration / total_chars if total_chars > 0 else 1.0

    current_time = 0.0

    # Добавляем каждое предложение как отдельную строку субтитров
    for sentence in sentences:
        # Разбиваем предложение на строки с учетом max_words_per_line
        words = sentence.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words_per_line:
                lines.append(" ".join(current_line))
                current_line = []

        if current_line:
            lines.append(" ".join(current_line))

        # Объединяем строки с переносами
        text = "\\N".join(lines)

        # Вычисляем длительность субтитра
        duration = len(sentence) * char_duration
        duration = max(duration, 1.0)  # Минимальная длительность 1 секунда

        start_time = current_time
        end_time = start_time + duration
        current_time = end_time + 0.1  # Небольшой промежуток между субтитрами

        # Добавляем строку субтитров
        dialogue_line = f"Dialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{text}\n"
        ass_content += dialogue_line

    # Записываем в файл
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_file


def generate_typewriter_effect(text: str, output_file: str, duration: float = 5.0,
                               font: str = "Arial", font_size: int = 48, color: str = "&HFFFFFF",
                               stroke_width: int = 2, stroke_color: str = "&H000000",
                               alignment: int = 5) -> str:
    """
    Генерирует файл субтитров ASS с эффектом печатной машинки

    Args:
        text: Текст для отображения
        output_file: Путь к выходному файлу
        duration: Длительность эффекта в секундах
        font: Шрифт
        font_size: Размер шрифта
        color: Цвет текста в формате ASS (&HRRGGBB)
        stroke_width: Толщина обводки
        stroke_color: Цвет обводки в формате ASS (&HRRGGBB)
        alignment: Позиция (1-9, как на цифровой клавиатуре)

    Returns:
        Путь к созданному файлу субтитров
    """
    # Создаем заголовок ASS файла
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{color},&H00FFFFFF,{stroke_color},&H00000000,0,0,0,0,100,100,0,0,1,{stroke_width},0,{alignment},20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
        font=font,
        font_size=font_size,
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        alignment=alignment
    )

    # Вычисляем задержку для каждого символа
    char_delay = duration / len(text) if len(text) > 0 else 0.1

    # Создаем эффект печатной машинки с помощью тегов \k
    k_tags = ""
    for _ in text:
        k_tags += f"\\k{int(char_delay * 100)}"

    # Добавляем строку субтитров
    dialogue_line = f"Dialogue: 0,0:00:00.00,{format_time(duration + 2.0)},Default,,0,0,0,,{{{k_tags}}}{text}\n"
    ass_content += dialogue_line

    # Записываем в файл
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_file
