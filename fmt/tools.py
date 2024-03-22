import json
from typing import Union


def load_slim_map(reversed_map: Union[str, dict], original_map: Union[str, dict]) -> dict:
    """
    for key in original_map,
    if key not in reversed_map.values(),
    delete key from original_map
    """
    if isinstance(reversed_map, str):
        with open(reversed_map, 'r', encoding='utf-8') as f:
            reversed_map = json.load(f)
    if isinstance(original_map, str):
        with open(original_map, 'r', encoding='utf-8') as f:
            original_map = json.load(f)

    # DO NOT DO THIS
    # for key in list(reversed_map.keys()):
    #     if key not in reversed_map.values():
    #         original_map.pop(key)
    # Python iteration is horribly slow
    # This can take up to 20 minutes

    new_map = {}
    for key in reversed_map.values():
        new_map[key] = original_map.get(key, '')
        # yes, text maps are not guaranteed to have identical keys
        # e.g. 3596235320 in Ver. 4.5

    return new_map
