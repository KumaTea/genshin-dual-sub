from ovl.init import pygame
from ovl.tools import draw
from ovl.configs import FPS
from ovl.session import clock
from ovl.init import screen, unused_color


def test(s):
    s.fill(unused_color)  # Transparent background
    draw(s, [['路', 'ル'], ['比', 'ビ'], ['ちゃんって、', ''], ['大好', 'だいす'], ['き', ''], ['だ', '']])
    pygame.display.update()
    is_running = True
    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    test(screen)
