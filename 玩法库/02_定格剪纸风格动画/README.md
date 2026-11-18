# 02｜小红帽定稿动画 Skill

[返回玩法库首页](../../README.md) · [打开 Skill](skill/continuous-stop-motion-gif/SKILL.md)

《小红帽 · 门后的影子》的 22 秒定稿制作流程：树后换装、戴眼镜、敲门、屋内偷看、开门、影子先变、真身揭晓与狼的反应。用十二张纸雕素材和分层代码复现十镜头短片，并以同一时间线驱动拟音。

本目录只发布这个 Skill，以及复现必需的源素材、脚本和实际提示词。运行后可生成 1600×900 带声 MP4 与 GIF；成片、帧缓存和历史版本不随包上传。

## 使用

将 `skill/continuous-stop-motion-gif` 完整复制到项目的 `.agents/skills/`，然后发送：

```text
使用 $continuous-stop-motion-gif，复现小红帽定稿动画。
保持十镜头叙事、影子先变和同步拟音，交付 MP4 与 GIF。
```

直接用 Python 复现时，按 [定稿工程说明](skill/continuous-stop-motion-gif/references/final-case.md) 复制工程到工作目录再运行。依赖为 Pillow、NumPy、OpenCV 和已有 FFmpeg（或 imageio-ffmpeg）。制作新故事需要适配素材与坐标。

当前包延续既有 `continuous-stop-motion-gif` 名称，内置工程更新为这次小红帽定稿。模型编写合成代码、图像工具生成资产、FFmpeg 编码的职责分别记录。实际试听未完成，不能将技术检查视为听感验收。
