import pygame
import win32api
import win32con
import win32gui
from share.session import config
from pygame._sdl2.video import Window


pygame.init()

# set resolution
screen = pygame.display.set_mode((int(config['general']['width']), int(config['overlay']['ovl_h'])), pygame.NOFRAME)

# set position
window = Window.from_display_module()
window.position = (0, int(config['general']['height']) - int(config['overlay']['ovl_h']))


# make window transparent
# https://stackoverflow.com/a/51845075/10714490

# pick an unused color
unused_color = (0, 0, 0)

# Create layered window
hwnd = pygame.display.get_wm_info()["window"]
win32gui.SetWindowLong(
    hwnd,
    win32con.GWL_EXSTYLE,
    win32gui.GetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE
    ) | win32con.WS_EX_LAYERED
)

# Set window transparency color
win32gui.SetLayeredWindowAttributes(
    hwnd, win32api.RGB(*unused_color),
    0,
    win32con.LWA_COLORKEY
)

# set always on top
SetWindowPos = win32gui.SetWindowPos
SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
