from share.session import config

dialog_area = {
    '2560x1440': (430, 1210, 2130, 1315),
    '2560x1080': (450, 890, 2110, 1010),
    '1920x1080': (320, 900, 1600, 1025),
}

rects = {
    '2560x1440': (0, 0, 2560, 120),
    '2560x1080': (0, 0, 2560, 120),
    '1920x1080': (0, 0, 1920, 120),
}

# FONT_PATH = config['game']['data_path'] + '\StreamingAssets\MiHoYoSDKRes\HttpServerResources\font\zh-cn.ttf'
FONT_PATH = config['game']['data_path'] + r'\StreamingAssets\MiHoYoSDKRes\HttpServerResources\font\ja-jp.ttf'

FPS = 10
