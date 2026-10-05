import logging

from apscheduler.schedulers.background import BackgroundScheduler

from share.config import settings

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=getattr(logging, settings.get('general', 'log_level').upper(), logging.INFO),
    datefmt='%Y-%m-%d %H:%M:%S')

# 第三方库的日志太吵
logging.getLogger('ppocr').setLevel(logging.ERROR)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

scheduler = BackgroundScheduler()

# 兼容旧代码：config['general']['data_path'] 仍可用
config = settings.parser
