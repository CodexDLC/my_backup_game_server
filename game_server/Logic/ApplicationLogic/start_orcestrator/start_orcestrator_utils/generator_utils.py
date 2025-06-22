
import re
from typing import Any, Dict, Generator, List, Optional
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


def generate_item_code(category: str, base_code: str, specific_name: str, material_code: str, suffix_code: str, rarity_level: int) -> str:
    category = str(category).upper()
    base_code = str(base_code).upper()
    specific_name = str(specific_name).upper()
    material_code = str(material_code).upper()
    suffix_code = str(suffix_code).upper()
    specific_name_sanitized = re.sub(r'[^A-Z0-9]+', '-', specific_name).strip('-')
    return f"{category}_{base_code}-{specific_name_sanitized}_{material_code}__{suffix_code}_R{rarity_level}"

def parse_item_code(item_code: str) -> Optional[Dict[str, str]]:
    pattern = re.compile(
        r'^(?P<category>[A-Z]+)_'
        r'(?P<base_code>[A-Z0-9_]+)-'
        r'(?P<specific_name>[A-Z0-9-]+)_'
        r'(?P<material_code>[A-Z0-9_]+)__'
        r'(?P<suffix_code>[A-Z0-9_]+)_'
        r'R(?P<rarity_level>\d+)$'
    )
    match = pattern.match(item_code)
    return match.groupdict() if match else None
