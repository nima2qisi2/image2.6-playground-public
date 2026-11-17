# Cinematic Title Director

用 CT-01 至 CT-32 选择电影片头或品牌标题的字形、构图和光线，输入自己的文字，生成对应视觉。

[打开 32 款成品画廊](preview.html) · [按编号查提示词](catalog/index.md)

以下为以 DMIAO 为主题的 AI 生成预览，CT-27 沿用 DMIAO COFFEE 横稿。点击每张图片可看原图。生成字形以成图为准，用户可以选择后期用授权字体重新排字。

| **CT-01 星际孤境**<br>[![CT-01](assets/previews/ct-01.png)](assets/previews/ct-01.png) | **CT-02 大理石王朝**<br>[![CT-02](assets/previews/ct-02.png)](assets/previews/ct-02.png) | **CT-03 雾林倒影**<br>[![CT-03](assets/previews/ct-03.png)](assets/previews/ct-03.png) | **CT-04 绯红丝绒**<br>[![CT-04](assets/previews/ct-04.png)](assets/previews/ct-04.png) |
|---|---|---|---|
| **CT-05 监墙刻痕**<br>[![CT-05](assets/previews/ct-05.png)](assets/previews/ct-05.png) | **CT-06 落日签名**<br>[![CT-06](assets/previews/ct-06.png)](assets/previews/ct-06.png) | **CT-07 雪峰星标**<br>[![CT-07](assets/previews/ct-07.png)](assets/previews/ct-07.png) | **CT-08 深水低语**<br>[![CT-08](assets/previews/ct-08.png)](assets/previews/ct-08.png) |
| **CT-09 野花恋曲**<br>[![CT-09](assets/previews/ct-09.png)](assets/previews/ct-09.png) | **CT-10 灰城前线**<br>[![CT-10](assets/previews/ct-10.png)](assets/previews/ct-10.png) | **CT-11 日蚀留白**<br>[![CT-11](assets/previews/ct-11.png)](assets/previews/ct-11.png) | **CT-12 双色霓虹**<br>[![CT-12](assets/previews/ct-12.png)](assets/previews/ct-12.png) |
| **CT-13 王室金字**<br>[![CT-13](assets/previews/ct-13.png)](assets/previews/ct-13.png) | **CT-14 复古红光**<br>[![CT-14](assets/previews/ct-14.png)](assets/previews/ct-14.png) | **CT-15 荒原工业**<br>[![CT-15](assets/previews/ct-15.png)](assets/previews/ct-15.png) | **CT-16 废城求生**<br>[![CT-16](assets/previews/ct-16.png)](assets/previews/ct-16.png) |
| **CT-17 极简轨道**<br>[![CT-17](assets/previews/ct-17.png)](assets/previews/ct-17.png) | **CT-18 度假讽喻**<br>[![CT-18](assets/previews/ct-18.png)](assets/previews/ct-18.png) | **CT-19 冷调侧写**<br>[![CT-19](assets/previews/ct-19.png)](assets/previews/ct-19.png) | **CT-20 政局暗线**<br>[![CT-20](assets/previews/ct-20.png)](assets/previews/ct-20.png) |
| **CT-21 海浪笔刷**<br>[![CT-21](assets/previews/ct-21.png)](assets/previews/ct-21.png) | **CT-22 暗潮家族**<br>[![CT-22](assets/previews/ct-22.png)](assets/previews/ct-22.png) | **CT-23 棋局古典**<br>[![CT-23](assets/previews/ct-23.png)](assets/previews/ct-23.png) | **CT-24 幻城鎏金**<br>[![CT-24](assets/previews/ct-24.png)](assets/previews/ct-24.png) |
| **CT-25 数字残影**<br>[![CT-25](assets/previews/ct-25.png)](assets/previews/ct-25.png) | **CT-26 荒野手记**<br>[![CT-26](assets/previews/ct-26.png)](assets/previews/ct-26.png) | **CT-27 沙丘几何**<br>[![CT-27](assets/previews/ct-27.png)](assets/previews/ct-27.png) | **CT-28 暗巷重字**<br>[![CT-28](assets/previews/ct-28.png)](assets/previews/ct-28.png) |
| **CT-29 仪式烛火**<br>[![CT-29](assets/previews/ct-29.png)](assets/previews/ct-29.png) | **CT-30 声波取证**<br>[![CT-30](assets/previews/ct-30.png)](assets/previews/ct-30.png) | **CT-31 雨玻璃折裂**<br>[![CT-31](assets/previews/ct-31.png)](assets/previews/ct-31.png) | **CT-32 风暴海岸**<br>[![CT-32](assets/previews/ct-32.png)](assets/previews/ct-32.png) |

## 使用
将整个仓库目录命名为 cinematic-title-director，放入支持本地 Skill 的工具的技能目录。也可以直接复制 prompts 中的英文提示词，替换 TITLE、FORMAT 和 ASPECT_RATIO。

例如“CT-11 DMIAO”，沿用该款横幅日蚀构图。“CT-27，标题换成 DMIAO COFFEE，做 16:9 品牌海报”，按标题长度安排主副行。

[Skill 入口](SKILL.md) · [字体候选](fonts/verified-ofl-candidates.csv) · [素材及许可](NOTICE.md) · [生成记录](assets/manifest.json) · [MIT 许可](LICENSE)

维护时运行 python scripts/build_catalog.py，校验文件哈希并重建画廊、目录及 ZIP。


## 使用说明与案例

[完整使用方法、素材来源和注意事项](使用与案例.md) · [5 秒案例轮播](assets/dmiao-32-styles-5s.gif)

![32 款案例轮播](assets/dmiao-32-styles-5s.gif)
