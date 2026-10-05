from ocr.gs.dialog import send_dialog_text
from ocr.gs.info import check_genshin_foreground, check_genshin_info
from ocr.gs.status import check_talking
from share.config import settings
from share.session import scheduler


def add_ocr_jobs() -> None:
    # 先立刻跑一遍，不然启动后要等一个周期字幕才出来
    check_genshin_info()
    check_genshin_foreground()

    jobs = (
        (check_genshin_info, 'genshin_info'),
        (check_genshin_foreground, 'genshin_fg'),
        (check_talking, 'talking'),
        (send_dialog_text, 'dialog'),
    )
    for func, key in jobs:
        scheduler.add_job(
            func, 'interval',
            seconds=max(0.05, settings.float('intervals', key)),
            max_instances=1,
            # OCR 偶尔会比调度间隔慢，攒着的任务直接丢掉，别排队
            coalesce=True,
            misfire_grace_time=1,
        )
