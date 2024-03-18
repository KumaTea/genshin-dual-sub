import logging
import configparser
from apscheduler.schedulers.background import BackgroundScheduler


config = configparser.ConfigParser(allow_no_value=True)
config.read(f'config.ini', encoding='utf-8')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# disable ppocr logs
logging.getLogger('ppocr').setLevel(logging.ERROR)

scheduler = BackgroundScheduler()
scheduler.start()
