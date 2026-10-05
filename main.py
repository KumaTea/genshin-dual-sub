"""原神双语字幕。

启动流程：准备数据 -> 载入索引 -> 起后台 OCR 任务 -> 进主循环。

原来的 main.py 是在 import 之间穿插调用的（先 `init()` 再 import 其他模块），
因为那些模块在 import 时就会读文件、加载模型。现在这些副作用都收进了函数里，
import 顺序不再有讲究。
"""

import argparse
import logging
import sys


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='原神双语字幕')
    parser.add_argument('--lang', help='第二字幕语言，覆盖 config.ini 的设置')
    parser.add_argument('--download', action='store_true',
                        help='允许在缺少文本数据时自动下载')
    parser.add_argument('--prepare-only', action='store_true',
                        help='只准备数据，不显示字幕')
    parser.add_argument('--ignore-foreground', action='store_true',
                        help='游戏不在前台时也持续识别')
    parser.add_argument('--region',
                        help='固定抓取区域 left,top,right,bottom，不再跟随游戏窗口')
    parser.add_argument('--log-level', help='DEBUG / INFO / WARNING / ERROR')
    return parser.parse_args(argv)


def prepare(args: argparse.Namespace) -> bool:
    from cpl.process import init
    from fmt import session as fmt_session
    from lev.session import lev
    from share.config import settings

    settings.save_if_incomplete()

    if args.lang:
        settings.set('general', 'dst_lang', args.lang)
    if args.download:
        settings.set('download', 'allow_download', 1)
    if args.ignore_foreground:
        settings.set('game', 'require_foreground', 0)
    if args.region:
        settings.set('game', 'capture_region', args.region)
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())

    if not init():
        return False

    lev.load()
    fmt_session.load()
    return True


def main(argv=None) -> int:
    args = parse_args(argv)

    from share import session  # noqa: F401  配置日志

    if not prepare(args):
        logging.error('[APP]\t数据未就绪，无法启动')
        return 1

    if args.prepare_only:
        logging.info('[APP]\t数据准备完成')
        return 0

    from ocr.manager import add_ocr_jobs
    from ovl.app import Application
    from share.session import scheduler

    application = Application()
    scheduler.start()
    add_ocr_jobs()
    application.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
