"""文本数据下载。

数据来自 Dimbreath 的 animegamedata2，作者没有声明许可协议，
所以**默认不下载**：要么用户自己下好放进 data/，要么明确同意后由程序代劳。
同意状态可以记在 config.ini 的 download.allow_download 里，下次就不再问。

注意分支是 main，不是 master——旧代码里那几个 master 链接现在都是 404。
"""

import logging
import os
import shutil
import sys
import time
import urllib.error
import urllib.request

from share.config import settings

USER_AGENT = 'genshin-dual-sub'
CHUNK = 1 << 20  # 1 MiB


def base_url() -> str:
    return settings.get('download', 'base_url').rstrip('/')


def file_url(filename: str) -> str:
    return f'{base_url()}/{filename}?inline=false'


def _format_size(size: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.1f}{unit}'
        size /= 1024
    return f'{size:.1f}GB'


def ask_consent(filenames: list[str]) -> bool:
    """询问用户是否允许下载。非交互环境（没有 tty）一律视为不允许。"""
    if settings.bool('download', 'allow_download'):
        return True

    if not sys.stdin or not sys.stdin.isatty():
        logging.error('[DL]\t缺少文本数据，且当前不是交互式终端，无法询问下载许可')
        return False

    print()
    print('  需要以下文本数据文件：')
    for name in filenames:
        print(f'    - {name}')
    print(f'  下载地址：{base_url()}')
    print('  数据来自 Dimbreath/animegamedata2，作者未声明许可协议，')
    print('  因此需要你明确同意后才会下载。总大小约 150MB。')
    print()

    try:
        answer = input('  是否允许下载？(y = 本次允许 / a = always 以后都允许 / 其他 = 否): ')
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    answer = answer.strip().lower()
    if answer == 'a':
        settings.set('download', 'allow_download', 1)
        settings.save()
        return True
    return answer in ('y', 'yes')


def download_file(filename: str, target_dir: str) -> bool:
    """下载单个文件。先写 .part 再改名，中断了不会留下半个文件被当成完整数据。"""
    url = file_url(filename)
    target = os.path.join(target_dir, filename)
    partial = target + '.part'

    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            total = int(response.headers.get('Content-Length') or 0)
            done = 0
            started = time.monotonic()
            with open(partial, 'wb') as f:
                while True:
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    _progress(filename, done, total, time.monotonic() - started)
        print()
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        print()
        logging.error(f'[DL]\t下载 {filename} 失败：{e}')
        if os.path.exists(partial):
            os.remove(partial)
        return False

    shutil.move(partial, target)
    logging.info(f'[DL]\t{filename} 下载完成')
    return True


def _progress(filename: str, done: int, total: int, elapsed: float) -> None:
    speed = done / elapsed if elapsed > 0 else 0
    if total:
        percent = done * 100 / total
        bar_width = 24
        filled = int(bar_width * done / total)
        bar = '#' * filled + '-' * (bar_width - filled)
        line = (f'  {filename:28s} [{bar}] {percent:5.1f}% '
                f'{_format_size(done)}/{_format_size(total)} {_format_size(speed)}/s')
    else:
        line = f'  {filename:28s} {_format_size(done)} {_format_size(speed)}/s'
    print(f'\r{line}', end='', flush=True)


def download_missing(filenames: list[str], target_dir: str) -> list[str]:
    """下载缺失的文件，返回仍然缺失的文件名。"""
    missing = [n for n in filenames if not os.path.exists(os.path.join(target_dir, n))]
    if not missing:
        return []

    if not ask_consent(missing):
        return missing

    os.makedirs(target_dir, exist_ok=True)
    logging.info(f'[DL]\t开始下载 {len(missing)} 个文件到 {target_dir}')
    still_missing = []
    for name in missing:
        if not download_file(name, target_dir):
            still_missing.append(name)
    return still_missing
