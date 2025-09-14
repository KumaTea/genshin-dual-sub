# Genshin Dual Sub

原神双语字幕

![preview](https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dfb932e2-bbbd-49e6-80f7-1355dca98b3b)

### 如何使用

> [!WARNING]
> 该项目还在开发的初期阶段，非常不稳定，当前仅供个人学习使用

1. 安装 [uv](https://docs.astral.sh/uv/)
2. `uv run python main.py`

### 亮点

* 低占用 (<5% CPU)
* 支持日语汉字注音 / ruby text
* 替换各种代词、昵称以更精确匹配

https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dddd16ec-64ef-47cc-b01e-cb56796ca30e

* 灵感来源 [qew21 / GI-Subtitles](https://github.com/qew21/GI-Subtitles)
* 数据来源 [Dimbreath / AnimeGameData](https://gitlab.com/Dimbreath/AnimeGameData/-/tree/master/TextMap)

### 原理

| 步骤 | 工具 | 说明 |
|---|---|---|
| 0 | | [格式化](https://github.com/KumaTea/genshin-dual-sub/tree/main/cpl)原始文本数据 | |
| 1 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | [识别](https://github.com/KumaTea/genshin-dual-sub/tree/main/ocr)游戏内字幕 |
| 2 | [Levenshtein](https://github.com/rapidfuzz/Levenshtein) | [计算](https://github.com/KumaTea/genshin-dual-sub/tree/main/lev)字幕相似度 |
| 3.1 | [Pykakasi](https://codeberg.org/miurahr/pykakasi) | [注音](https://github.com/KumaTea/genshin-dual-sub/tree/main/fmt) |
| 3.2 | | 再次格式化匹配字幕数据 |
| 4 | [Pygame](https://github.com/pygame/pygame) | [显示](https://github.com/KumaTea/genshin-dual-sub/tree/main/ovl)字幕 |

### 开发计划

- [ ] 大众友好的启动器
- [ ] 允许移动字幕位置
- [ ] 支持更多语言
- [ ] 支持同时标注官方上标及读音
- [ ] 格式化图片 (灰度 / 提取仅白色) 以优化识别效果
