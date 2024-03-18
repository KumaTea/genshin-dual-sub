from ovl.tools import draw
from ovl.session import overlay, pygame
from ovl.init import screen, unused_color
from share.session import scheduler, config


def draw_text(s):
    s.fill(unused_color)  # Transparent background
    draw(s, overlay.text)
    pygame.display.update()


def clean_screen() -> None:
    screen.fill(unused_color)
    pygame.display.update()


def check_draw() -> None:
    if overlay.need_update:
        if overlay.text:
            draw_text(screen)
            overlay.need_update = False
        else:
            clean_screen()


def add_ovl_jobs() -> None:
    scheduler.add_job(check_draw, 'interval', seconds=float(config['intervals']['draw']))
