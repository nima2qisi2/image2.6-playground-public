# 数字成长档案 Skill

[返回玩法](../../README.md) · [海马案例](../../案例/海马_v21/README.md)

`specimen-growth-archive` 是一套制作数字档案海报和成长动画的流程说明，包含海马 v21 基准素材与本地渲染脚本。技能指导与示例脚本的边界见 [SKILL.md](SKILL.md)。

## 你需要准备

- 自己的主体、不同阶段的独立图片，或描述明确的阶段素材需求。
- 说明哪些是需要保留的主体，哪些是版式、构图或动作参考。
- 如需复跑海马案例：Python 3.10+、NumPy、Pillow、OpenCV；导出 GIF / MP4 还需 FFmpeg。
- 基准目前使用 Windows 字体 Arial、Arial Bold 和微软雅黑细体。其他系统需自行提供兼容字体并重新调整、检查版式；字体不随包提供。

## 安装

将 `specimen-growth-archive` 整个文件夹复制到 Codex 的技能目录，随后在新的会话中使用 `$specimen-growth-archive`。文件夹需要保留 `SKILL.md`、`references`、`scripts`、`assets` 等结构。安装技能不会自动安装 Python 依赖或生成模型。

## 复跑海马

具体命令、依赖和检查方法见 [海马基准复跑说明](references/seahorse-baseline.md)。先用 `preview` 查看，再按需运行 `keyframes` 或完整导出；输出目录应位于技能文件夹之外。

基准使用 720×960、五阶段海马素材。脚本未验证可直接处理其他物种，不能只替换图片或名称就宣称可用；新主体需重新准备形态、遮罩和对应点。

## 你可以这样说

```text
使用 $specimen-growth-archive，把我提供的五个阶段主体制作成数字成长档案。
保留主体的原始轮廓、纹理和关键结构；深色背景，细线与节点标注，输出 GIF 与 MP4。
```

需要真实物种、年龄或尺寸时，请提供可核实的资料；艺术化数字应标为示意。案例技术与视觉自检不代表用户已验收。
