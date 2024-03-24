from ocr.gs.status import check_talking
from ocr.gs.dialog import send_dialog_text  # , debug_dialog_text
from share.session import scheduler, config
from ocr.gs.info import check_genshin_info, check_genshin_foreground


def add_ocr_jobs() -> None:
    # do it now
    check_genshin_info()
    check_genshin_foreground()
    check_talking()
    send_dialog_text()

    # add jobs
    scheduler.add_job(check_genshin_info, 'interval', seconds=int(config['intervals']['genshin_info']))
    scheduler.add_job(check_genshin_foreground, 'interval', seconds=int(config['intervals']['genshin_fg']))
    scheduler.add_job(check_talking, 'interval', seconds=int(config['intervals']['talking']))
    scheduler.add_job(send_dialog_text, 'interval', seconds=int(config['intervals']['dialog']))
    # scheduler.add_job(debug_dialog_text, 'interval', seconds=2)
