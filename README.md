# Genshin Dual Sub

原神双语字幕

![preview](https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dfb932e2-bbbd-49e6-80f7-1355dca98b3b)

### 如何使用

> [!WARNING]
> 该项目还在开发的初期阶段，非常不稳定，当前仅供个人学习使用

1. 安装 [uv](https://docs.astral.sh/uv/)
2. `uv run python main.py`

首次运行会提示缺少文本数据。可以自己下载放进 `data/`，
也可以让程序代劳（需要明确同意，见下方[文本数据](#文本数据)）。

`config.ini` 会在首次运行时自动生成并补全，可参考 [config.ini.example](config.ini.example)。

### 操作

字幕默认锁定在屏幕底部、鼠标可穿透。托盘图标右键可以操作，也有快捷键：

| 快捷键 | 作用 |
|---|---|
| `Ctrl+Alt+M` | 锁定 / 解锁字幕，解锁后可以直接用鼠标拖动 |
| `Ctrl+Alt+方向键` | 微调字幕位置 |
| `Ctrl+Alt+PgUp` / `PgDn` | 背景不透明度 ±10% |
| `Ctrl+Alt+H` | 显示 / 隐藏字幕 |
| `Ctrl+Alt+Q` | 退出 |

位置和不透明度会自动写回 `config.ini`。托盘菜单里还能切换「仅在游戏前台时工作」。

### 前台限制与固定抓取区域

默认只在原神处于前台时才抓屏识别：既省资源，也避免把挡在游戏上面的窗口识别进去。

需要一直工作时（窗口化游戏、双屏、一边看攻略一边挂字幕），有三种方式关掉这个限制：

* 托盘菜单取消勾选「仅在游戏前台时工作」
* `config.ini` 里设 `[game] require_foreground = 0`
* 启动时加 `--ignore-foreground`

如果连游戏窗口都找不到（串流、改过标题的客户端），可以直接指定抓取区域：

```ini
[game]
capture_region = 0,0,3840,2160
```

填了之后就不再跟随游戏窗口。注意要给**游戏画面的完整范围**，因为对话区位置是按
画面比例算出来的，只圈字幕那一条会算歪。

### 亮点

* 低占用 (<5% CPU)
* 支持日语汉字注音 / ruby text；相邻汉字的读音合并成整块，不会互相挤在一起
* 游戏自带上标（`{RUBY#...}`）优先于假名读音，两者不叠加
* 替换各种代词、昵称以更精确匹配
* 背景颜色与不透明度可调（0% ~ 100%）
* 自动适配分辨率，支持三种对话版式（剧情对话 / 闲聊 / 旁白通讯）

https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dddd16ec-64ef-47cc-b01e-cb56796ca30e

* 灵感来源 [qew21 / GI-Subtitles](https://github.com/qew21/GI-Subtitles)
* 数据来源 [Dimbreath / AnimeGameData](https://gitlab.com/Dimbreath/animegamedata2/-/tree/main/TextMap)

### 原理

| 步骤 | 工具 | 说明 |
|---|---|---|
| 0 | | [格式化](cpl)原始文本数据 |
| 1.1 | | 按说话人名字的颜色判断[对话版式](ocr/layout.py) |
| 1.2 | [RapidOCR](https://github.com/RapidAI/RapidOCR) + OpenVINO | [识别](ocr)游戏内字幕（先滤白再识别） |
| 2 | [Levenshtein](https://github.com/rapidfuzz/Levenshtein) | [计算](lev)字幕相似度 |
| 3.1 | [Pykakasi](https://codeberg.org/miurahr/pykakasi) | [注音](fmt) |
| 3.2 | | 再次格式化匹配字幕数据 |
| 4 | [Pygame](https://github.com/pygame/pygame) + Win32 | [显示](ovl)字幕（分层窗口，逐像素透明） |

#### 对话版式

游戏里有三种聊天版式，靠说话人名字的颜色区分，这个颜色不随角色和场景变化：

| 版式 | 名字颜色 | 说明 |
|---|---|---|
| `chat` | `#ffc300` | 剧情对话框，每行各自居中 |
| `idle` | `#f1b703` | 世界里 NPC 的闲聊，位置更高、字号更小 |
| `type2` | `#ccffff` | 旁白 / 通讯，整块居中但行内左对齐；剧情里和大世界里高度不同 |

各版式的正文区域按画面比例存放（见 [ocr/configs.py](ocr/configs.py)），
比例值实测自 `debug/` 下的截图，任意分辨率都能算出坐标。

### 文本数据

数据来自 [Dimbreath/animegamedata2](https://gitlab.com/Dimbreath/animegamedata2/-/tree/main/TextMap)，
作者没有声明许可协议，因此**默认不会自动下载**。

* 自己下载：把 `TextMapCHS.json`、`TextMap_MediumCHS.json` 以及目标语言的两个文件放进 `data/`
* 让程序下载：运行时会询问，或者在 `config.ini` 里设 `[download] allow_download = 1`，
  也可以 `uv run python main.py --download`

### 命令行参数

```bash
uv run python main.py --lang ja-jp --log-level DEBUG
```

| 参数 | 作用 |
|---|---|
| `--lang` | 第二字幕语言，覆盖配置文件 |
| `--download` | 允许在缺少文本数据时自动下载 |
| `--prepare-only` | 只准备数据，不显示字幕 |
| `--ignore-foreground` | 游戏不在前台时也持续识别 |
| `--region` | 固定抓取区域 `left,top,right,bottom` |
| `--log-level` | 日志级别 |

### 测试

```bash
uv run pytest
```

`debug/` 下的游戏截图会作为版式识别和 OCR 的测试用例，没有该目录时相关测试自动跳过。

### 已知限制

* 只抓主显示器，游戏在副屏上不工作
* 不处理系统缩放（DPI scaling），建议缩放设为 100%

以上两项暂无支持计划。

### 开发计划

- [ ] 大众友好的启动器（已有托盘图标，仍需打包分发）
- [x] 允许移动字幕位置
- [x] 支持更多语言
- [x] 标注游戏官方上标及读音
- [x] 格式化图片 (灰度 / 提取仅白色) 以优化识别效果
- [ ] 对话文本流式匹配，减少逐字显字过程中的重复识别
