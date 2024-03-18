from ovl.init import pygame
from ovl.configs import FPS
from cpl.process import init
from ovl.session import clock
from ocr.manager import add_ocr_jobs
from ovl.manager import add_ovl_jobs


init()
add_ocr_jobs()
add_ovl_jobs()


if __name__ == '__main__':
    is_running = True
    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
        clock.tick(FPS)
    pygame.quit()
