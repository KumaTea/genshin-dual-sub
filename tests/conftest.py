import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEBUG_DIR = os.path.join(ROOT, 'debug')


@pytest.fixture(scope='session')
def debug_dir() -> str:
    if not os.path.isdir(DEBUG_DIR):
        pytest.skip('缺少 debug/ 截图')
    return DEBUG_DIR


def screenshot_path(name: str) -> str:
    return os.path.join(DEBUG_DIR, name)


def has_screenshots() -> bool:
    return os.path.isdir(DEBUG_DIR) and bool(os.listdir(DEBUG_DIR))
