"""主循环与收尾。

主线程只做两件事：抽 Windows 消息（托盘、快捷键、拖动），
以及按刷新率重画字幕。OCR、匹配这些耗时的活都在 APScheduler 的后台线程里。
"""

import logging
import signal
import time
from typing import Optional

from ovl.configs import FPS
from ovl.manager import get_manager
from ovl.session import overlay
from ovl.tray import HOTKEY_HELP, TrayApp, get_app
from share.config import settings
from share.session import scheduler

NUDGE_STEP = 10
OPACITY_STEP = 10
# 消息抽取的频率，比刷新率高，拖动才跟手
PUMP_HZ = 60


class Application:
    def __init__(self):
        self.manager = get_manager()
        self.tray: Optional[TrayApp] = None
        self._running = True

    # ------------------------------------------------------------ 动作

    def _actions(self) -> dict:
        manager = self.manager
        return {
            'state': lambda: {
                'visible': overlay.visible,
                'locked': manager.window.locked,
                'bg_opacity': overlay.bg_opacity,
                'require_foreground': settings.bool('game', 'require_foreground'),
            },
            'toggle_lock': manager.toggle_locked,
            'toggle_visible': manager.toggle_visible,
            'reset_position': manager.reset_position,
            'set_opacity': manager.set_bg_opacity,
            'opacity_up': lambda: manager.step_bg_opacity(OPACITY_STEP),
            'opacity_down': lambda: manager.step_bg_opacity(-OPACITY_STEP),
            'nudge_up': lambda: manager.nudge(0, -NUDGE_STEP),
            'nudge_down': lambda: manager.nudge(0, NUDGE_STEP),
            'nudge_left': lambda: manager.nudge(-NUDGE_STEP, 0),
            'nudge_right': lambda: manager.nudge(NUDGE_STEP, 0),
            'toggle_foreground': self.toggle_foreground,
            'quit': self.stop,
        }

    def toggle_foreground(self) -> bool:
        """切换"只在游戏前台时工作"。

        关掉之后即使游戏在后台也照常抓屏识别，代价是 CPU 占用一直在，
        而且游戏被别的窗口挡住时会识别到挡住它的东西。
        """
        require = not settings.bool('game', 'require_foreground')
        settings.set('game', 'require_foreground', int(require))
        settings.save()
        logging.info(f'[APP]	{"仅在游戏前台时工作" if require else "忽略游戏前台状态，持续识别"}')
        if not require:
            # 立刻生效，不用等下一轮前台检测
            from ocr.gs.info import check_genshin_foreground
            check_genshin_foreground()
        return require

    def stop(self, *_) -> None:
        if self._running:
            logging.info('[APP]\t正在退出…')
        self._running = False
        if self.tray:
            self.tray.stop()

    # ------------------------------------------------------------ 循环

    def run(self) -> None:
        self.tray = get_app(self._actions())

        # 控制台的 Ctrl+C 也走同一条收尾路径
        signal.signal(signal.SIGINT, self.stop)
        try:
            signal.signal(signal.SIGTERM, self.stop)
        except (ValueError, AttributeError):
            pass

        logging.info('[APP]\t已启动，托盘图标可退出')
        for line in HOTKEY_HELP.splitlines():
            logging.info(f'[APP]\t{line}')

        pump_interval = 1 / PUMP_HZ
        draw_interval = 1 / max(1, FPS)
        next_draw = 0.0
        next_sync = 0.0

        try:
            while self._running:
                if self.tray and not self.tray.pump():
                    break

                now = time.monotonic()
                if now >= next_draw:
                    self.manager.draw_if_needed()
                    next_draw = now + draw_interval
                if now >= next_sync:
                    # 拖动结束后把新位置写回配置
                    self.manager.sync()
                    next_sync = now + 1.0

                time.sleep(pump_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        from ocr.screenshot import release_camera

        try:
            if scheduler.running:
                scheduler.shutdown(wait=False)
        except Exception:
            logging.debug('[APP]\t关闭调度器时出错', exc_info=True)

        release_camera()

        if self.tray:
            self.tray.close()
        self.manager.close()
        settings.save()
        logging.info('[APP]\t已退出')
