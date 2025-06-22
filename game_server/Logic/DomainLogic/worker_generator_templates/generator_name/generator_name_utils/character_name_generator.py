# game_server/Logic/InfrastructureLogic/generator/name_generator/character_name_generator.py

import random
from typing import List, Tuple, Dict

class CharacterNameGenerator:
    """
    Класс для генерации имен и фамилий персонажей (людей) на основе корней и суффиксов.
    Учитывает фонетические правила для славянских имен и фамилий.
    """
    # --- Корни и суффиксы для ИМЕН ---
    _MALE_ROOTS_CONSONANT_END: List[str] = [
        "Влад", "Добр", "Люд", "Бори", "Мир", "Свят", "Буд", "Держ", "Тверд", "Мсти", "Злат", "Все", "Радо"
    ]
    _MALE_ROOTS_VOWEL_END: List[str] = [
        "Яро", "Свято", "Миро", "Все", "Радо", "Славо", "Зори", "Любо", "Госто", "Туго"
    ]
    _MALE_SUFFIXES: List[str] = [
        "слав", "мир", "полк", "вой", "бор", "дух", "мысл", "яр", "дан", "вид", "гост"
    ]
    _MALE_ENDINGS: List[str] = ["", "й", "н", "рь", "н", "л"] # Для односоставных имен (Ждан, Орел)

    _FEMALE_ROOTS: List[str] = [
        "Яро", "Свято", "Владо", "Миро", "Добро", "Все", "Радо", "Славо", "Людмило",
        "Люба", "Наде", "Веро", "Злата", "Свето", "Краса", "Дарь", "Мари", "Ждан"
    ]
    _FEMALE_SUFFIXES: List[str] = [
        "слава", "мира", "мила", "яна", "дана", "лика", "ника", "мира", "слада"
    ]
    _FEMALE_ENDINGS: List[str] = ["а", "я", "ина", "ана", "ея", "она", "ора"]

    # Соединительные гласные для имен
    _LINKING_VOWELS_NAME: List[str] = ["и", "о", "е"]

    # --- Корни и суффиксы для ФАМИЛИЙ (собирательные для славянских народов) ---
    _SURNAME_ROOTS_CATEGORIZED: Dict[str, List[str]] = {
        "profession": [
            "Кузнец", "Портн", "Мельник", "Кожемяк", "Пекар", "Столяр", "Плотник",
            "Гончар", "Кравч", "Бондар", "Колесник", "Ткач", "Рыбак", "Слесар", "Сапожн" # Сапожник
        ],
        "animal": [
            "Волк", "Медвед", "Орлов", "Зайц", "Сокол", "Лисиц", "Комар", "Жуков", "Лис", "Солов" # Соловей
        ],
        "object_nature": [
            "Мороз", "Цвет", "Гриб", "Берёз", "Дуб", "Калин", "Клен", "Сосн", "Ряб",
            "Вишн", "Яблон", "Орех", "Стол", "Утюг", "Гвоздь", "Сосуль" # Сосулька
        ],
        "adjective": [
            "Черн", "Бел", "Высоц", "Красн", "Светл", "Гром", "Тиш", "Добр", "Храбр", "Жур"
        ],
        "name_derived": [ # Корни от имен, могут быть основой для фамилий
            "Иван", "Петр", "Степан", "Богдан", "Демьян", "Василь", "Григор", "Алекс"
        ]
    }

    # Суффиксы для "посессивных" фамилий (от профессий, животных, предметов)
    _POSSESSIVE_MALE_SUFFIXES: List[str] = ["ов", "ев", "ин", "ын", "иков", "ников"]
    _POSSESSIVE_FEMALE_SUFFIXES: List[str] = ["ова", "ева", "ина", "ына", "икова", "никова"]

    # Общие суффиксы для остальных типов корней (прилагательные, имена, некоторые другие)
    _GENERAL_MALE_SURNAME_SUFFIXES: List[str] = [
        "ский", "цкий", "ич", "ович", "евич", "ук", "юк", "енко", "ко", "ыч", "ак", "ан", "ун", "ай", "ло", "ец"
    ]
    _GENERAL_FEMALE_SURNAME_SUFFIXES: List[str] = [
        "ская", "цкая", "ич", "ович", "евич", "ук", "юк", "енко", "ко", "ыч", "ак", "ана", "уна", "ай", "ло", "ец"
    ]
    
    # Соединительные гласные для фамилий
    _LINKING_VOWELS_SURNAME: List[str] = ["о", "е"] # "о" для большинства, "е" для мягких окончаний

    @classmethod
    def generate_full_name(cls, gender: str) -> Tuple[str, str]:
        """
        Генерирует полное имя (имя и фамилию) для персонажа (человека).
        Args:
            gender (str): Пол персонажа ('male', 'female', 'other').
        Returns:
            Tuple[str, str]: Кортеж из имени и фамилии.
        """
        first_name = cls._generate_name_by_gender(gender)
        last_name = cls._generate_surname_by_gender(gender)
        return first_name, last_name

    @classmethod
    def _generate_name_by_gender(cls, gender: str) -> str:
        """
        Внутренняя функция для выбора имени по полу, генерируемого из корней и суффиксов,
        с учетом фонетических правил.
        """
        generated_name_parts = []

        is_male = gender.lower() == 'male'
        is_female = gender.lower() == 'female'

        if is_male:
            use_consonant_root = random.random() < 0.5 # Шанс на корень с согласным окончанием
            
            if use_consonant_root and cls._MALE_ROOTS_CONSONANT_END:
                root = random.choice(cls._MALE_ROOTS_CONSONANT_END)
                if random.random() < 0.8 and cls._MALE_SUFFIXES:
                    suffix = random.choice(cls._MALE_SUFFIXES)
                    if root[-1] not in 'аеёиоуыэюя' and suffix[0] not in 'аеёиоуыэюя':
                        linking_vowel = random.choice(cls._LINKING_VOWELS_NAME)
                        generated_name_parts = [root, linking_vowel, suffix]
                    else:
                        generated_name_parts = [root, suffix]
                else:
                    generated_name_parts = [root, random.choice(cls._MALE_ENDINGS)]
            else:
                root = random.choice(cls._MALE_ROOTS_VOWEL_END)
                if random.random() < 0.8 and cls._MALE_SUFFIXES:
                    suffix = random.choice(cls._MALE_SUFFIXES)
                    generated_name_parts = [root, suffix]
                else:
                    generated_name_parts = [root, random.choice(cls._MALE_ENDINGS)]

        elif is_female:
            root = random.choice(cls._FEMALE_ROOTS)
            if random.random() < 0.7:
                suffix = random.choice(cls._FEMALE_SUFFIXES)
                generated_name_parts = [root, suffix]
            else:
                generated_name_parts = [root, random.choice(cls._FEMALE_ENDINGS)]
        elif gender.lower() == 'other':
            all_roots_consonant = cls._MALE_ROOTS_CONSONANT_END + [r for r in cls._FEMALE_ROOTS if r[-1] not in 'аеёиоуыэюя']
            all_roots_vowel = cls._MALE_ROOTS_VOWEL_END + [r for r in cls._FEMALE_ROOTS if r[-1] in 'аеёиоуыэюя']
            all_suffixes = cls._MALE_SUFFIXES + cls._FEMALE_SUFFIXES
            all_endings = cls._MALE_ENDINGS + cls._FEMALE_ENDINGS

            use_consonant_root = random.random() < 0.4

            if use_consonant_root and all_roots_consonant:
                root = random.choice(all_roots_consonant)
                if random.random() < 0.6 and all_suffixes:
                    suffix = random.choice(all_suffixes)
                    if root[-1] not in 'аеёиоуыэюя' and suffix[0] not in 'аеёиоуыэюя':
                        linking_vowel = random.choice(cls._LINKING_VOWELS_NAME)
                        generated_name_parts = [root, linking_vowel, suffix]
                    else:
                        generated_name_parts = [root, suffix]
                else:
                    generated_name_parts = [root, random.choice(all_endings)]
            else:
                root = random.choice(all_roots_vowel)
                if random.random() < 0.6 and all_suffixes:
                    suffix = random.choice(all_suffixes)
                    generated_name_parts = [root, suffix]
                else:
                    generated_name_parts = [root, random.choice(all_endings)]
        else:
            random_gender = random.choice(['male', 'female'])
            return cls._generate_name_by_gender(random_gender)

        full_name = "".join(generated_name_parts).capitalize()
        return full_name.strip()

    @classmethod
    def _generate_surname_by_gender(cls, gender: str) -> str:
        """
        Внутренняя функция для выбора фамилии по полу, генерируемой из корней и суффиксов,
        с учетом славянских фонетических правил и категорий корней.
        """
        generated_surname_parts = []
        
        is_male = gender.lower() == 'male'
        is_female = gender.lower() == 'female'

        # Случайным образом выбираем категорию корня
        root_category = random.choice(list(cls._SURNAME_ROOTS_CATEGORIZED.keys()))
        root = random.choice(cls._SURNAME_ROOTS_CATEGORIZED[root_category])

        suffix = ""
        # Определяем суффиксы в зависимости от категории корня
        if root_category in ["profession", "animal", "object_nature"]:
            if is_male:
                suffix = random.choice(cls._POSSESSIVE_MALE_SUFFIXES)
            elif is_female:
                suffix = random.choice(cls._POSSESSIVE_FEMALE_SUFFIXES)
            else: # 'other'
                suffix = random.choice(cls._POSSESSIVE_MALE_SUFFIXES + cls._POSSESSIVE_FEMALE_SUFFIXES)
            
            # Для этих типов корней, если корень заканчивается на 'ник' (например, Плотник)
            # и мы НЕ используем суффикс 'ников', то просто добавляем обычный possessive suffix
            # Если корень оканчивается на согласную и суффикс начинается на согласную, 
            # применяем общую логику связующей гласной, но для possessive suffixes это реже нужно.
            # Пример: Кузнец + ов = Кузнецов
            # Пример: Стол + ов = Столов
            # Пример: Сапожн (от Сапожник) + иков = Сапожникова (уже заложено в суффикс)
            # Простая конкатенация обычно работает хорошо для possessive suffixes,
            # так как большинство из них начинаются с гласных (ов, ев, ин, иков).
            # Однако, для универсальности, оставим проверку.
            if root[-1] not in 'аеёиоуыэюя' and suffix[0] not in 'аеёиоуыэюя':
                # Здесь можно добавить специфичные связующие гласные для этих суффиксов, если они нужны.
                # Пока что большинство этих комбинаций выглядят нормально без доп. гласной.
                # Например, Бондар + ский (общий) -> Бондарский. А Бондар + ов -> Бондаров.
                # Для 'иков'/'ников' гласная уже в суффиксе.
                # Пока не добавляем здесь принудительную связующую гласную, т.к. possessive суффиксы часто начинаются с гласной.
                generated_surname_parts = [root, suffix]
            else:
                generated_surname_parts = [root, suffix]

        else: # Для "adjective" и "name_derived" корней
            if is_male:
                suffix = random.choice(cls._GENERAL_MALE_SURNAME_SUFFIXES)
            elif is_female:
                suffix = random.choice(cls._GENERAL_FEMALE_SURNAME_SUFFIXES)
            else: # 'other'
                general_suffixes = cls._GENERAL_MALE_SURNAME_SUFFIXES + [s for s in cls._GENERAL_FEMALE_SURNAME_SUFFIXES if s not in cls._GENERAL_MALE_SURNAME_SUFFIXES]
                suffix = random.choice(general_suffixes)
            
            # Общая логика для соединительных гласных
            if root[-1] not in 'аеёиоуыэюя' and suffix[0] not in 'аеёиоуыэюя':
                linking_vowel = random.choice(cls._LINKING_VOWELS_SURNAME)
                generated_surname_parts = [root, linking_vowel, suffix]
            else:
                generated_surname_parts = [root, suffix]

        full_surname = "".join(generated_surname_parts).capitalize()
        
        return full_surname.strip()