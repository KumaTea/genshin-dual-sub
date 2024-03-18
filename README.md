# genshin-dual-sub

原神双语字幕

* 灵感来源 [qew21 / GI-Subtitles](https://github.com/qew21/GI-Subtitles)
* 数据来源 [Dimbreath / AnimeGameData](https://gitlab.com/Dimbreath/AnimeGameData/-/tree/main/TextMap)

## 原理

1. 格式化原始文本数据
2. PaddleOCR 识别游戏内字幕
3. Levenshtein 距离计算字幕相似度
4. Pykakasi 注音 + 再次格式化匹配字幕数据
5. Pygame 显示字幕
