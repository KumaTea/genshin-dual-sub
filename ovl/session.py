from ovl.init import pygame  # ensure pygame is initialized
from share.session import config
from ovl.configs import FONT_PATH, rects


class Overlay:
    def __init__(self):
        self.text: list[list[str, str]] = []
        self.need_update = False


overlay = Overlay()


# text config
font = pygame.font.Font(FONT_PATH, int(config['overlay']['font_size']))
ruby_font = pygame.font.Font(FONT_PATH, int(config['overlay']['ruby_size']))
rect = pygame.Rect(*rects[f"{config['general']['width']}x{config['general']['height']}"])

clock = pygame.time.Clock()
