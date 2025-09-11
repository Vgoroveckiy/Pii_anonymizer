import re
from typing import Dict, List, Set

import phonenumbers
from natasha import NamesExtractor, Segmenter, MorphVocab

from .config import COMMON_NAMES

# Преобразуем в множество для быстрого поиска
COMMON_NAMES_SET = set(COMMON_NAMES)

# Объединенный паттерн для телефонов
PHONE_PATTERN = (
    r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|"
    r"(?<!\d)(?:7|8)\d{10}(?!\d)|"
    r"(?<!\d)\d{10}(?!\d)"
)


def is_valid_name(name: str) -> bool:
    """Проверяет, является ли строка валидным именем

    Критерии валидности:
    1. Длина не менее 3 символов
    2. Содержит хотя бы одну гласную букву русского алфавита
    3. Начинается с заглавной буквы

    Args:
        name (str): Проверяемое имя

    Returns:
        bool: True если имя валидно, иначе False
    """
    return (
        len(name) >= 3
        and any(char in "аеёиоуыэюя" for char in name.lower())
        and name[0].isupper()
    )


class PIIExtractor:
    """
    Класс для извлечения PII-сущностей (имен и телефонов) из текста.

    Использует комбинацию:
    1. Natasha (NLP-библиотека) для извлечения имен
    2. phonenumbers для валидации телефонов
    3. Регулярные выражения для поиска телефонных номеров
    4. Эвристики для фильтрации имен

    Attributes:
        segmenter (Segmenter): Сегментатор текста для Natasha
        morph_vocab (MorphVocab): Морфологический словарь для Natasha
        names_extractor (NamesExtractor): Экстрактор имен из Natasha

    Пример использования:
        >>> extractor = PIIExtractor()
        >>> text = "Иван, тел. 89161234567"
        >>> result = extractor.extract_all(text)
        >>> print(result)
        {'name': ['Иван'], 'phone': ['89161234567']}
    """

    def __init__(self):
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()  # Требуется для NamesExtractor
        self.names_extractor = NamesExtractor(self.morph_vocab)

    def extract_names(self, text: str) -> List[str]:
        """
        Извлекает имена из текста, используя Natasha и эвристики.

        Args:
            text (str): Текст для анализа

        Returns:
            List[str]: Список уникальных найденных имен (без дубликатов)

        Процесс:
            1. Извлечение имен с помощью Natasha
            2. Фильтрация по словарю распространенных имен
            3. Проверка валидности имени
        """
        names: Set[str] = set()

        # Извлечение имен с помощью Natasha
        for span in self.names_extractor(text):
            name_text = text[span.start : span.stop]
            if is_valid_name(name_text):
                names.add(name_text)

        # Эвристика: слова с заглавной буквы из известного списка имен
        words = re.findall(r"\b[А-ЯЁ][а-яё]+\b", text)
        for word in words:
            if word.lower() in COMMON_NAMES_SET and is_valid_name(word):
                names.add(word)

        return list(names)

    def extract_phones(self, text: str) -> List[str]:
        """
        Извлекает номера телефонов из текста в оригинальном формате.

        Args:
            text (str): Текст для анализа

        Returns:
            List[str]: Список уникальных телефонных номеров в том формате,
                       в котором они были найдены в тексте (без дубликатов)

        Процесс:
            1. Использует библиотеку phonenumbers для поиска валидных номеров
            2. Дополнительно ищет по регулярному выражению
            3. Убирает дубликаты
        """
        phones = []

        # Поиск через phonenumbers
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, "RU"):
                phones.append(text[match.start : match.end])
        except Exception:
            pass

        # Поиск по объединенному шаблону
        phones.extend(m.group() for m in re.finditer(PHONE_PATTERN, text))

        return list(set(phones))

    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """
        Извлекает все типы PII-данных из текста.

        Args:
            text (str): Текст для анализа

        Returns:
            Dict[str, List[str]]: Словарь с двумя ключами:
                - "name": список уникальных имен
                - "phone": список уникальных телефонов

        Пример возвращаемого значения:
            {
                "name": ["Иван", "Мария"],
                "phone": ["89161234567", "+74951234567"]
            }
        """
        return {"name": self.extract_names(text), "phone": self.extract_phones(text)}


if __name__ == "__main__":
    extractor = PIIExtractor()
    test_text = "Контакты: Иван Петров, тел. 9991234567, 8(999)123-45-67"
    print(extractor.extract_all(test_text))

    # Тест на ложное срабатывание
    test_text2 = "Ты программировать умееш?"
    result = extractor.extract_all(test_text2)
    print(
        f"Тест на ложное срабатывание: {result}"
    )  # Ожидаем: {'name': [], 'phone': []}
