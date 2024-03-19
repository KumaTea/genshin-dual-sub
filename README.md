# Genshin Dual Sub

原神双语字幕

![preview](https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dfb932e2-bbbd-49e6-80f7-1355dca98b3b)

### 亮点

* 低占用 (<5% CPU)
* 支持日语汉字注音 / ruby text
* 替换各种代词、昵称以更精确匹配

https://github.com/KumaTea/genshin-dual-sub/assets/36222458/dddd16ec-64ef-47cc-b01e-cb56796ca30e

* 灵感来源 [qew21 / GI-Subtitles](https://github.com/qew21/GI-Subtitles)
* 数据来源 [Dimbreath / AnimeGameData](https://gitlab.com/Dimbreath/AnimeGameData/-/tree/main/TextMap)

### 原理

1. 格式化原始文本数据
2. PaddleOCR 识别游戏内字幕
3. Levenshtein 距离计算字幕相似度
4. Pykakasi 注音 + 再次格式化匹配字幕数据
5. Pygame 显示字幕

### 开发计划

- [ ] 大众友好的启动器
- [ ] 允许移动字幕位置
- [ ] 支持更多语言
- [ ] 支持同时标注官方上标及读音
