# SOLO｜单人三合一最终生图提示词

将方括号参数替换为**本轮已核实素材**；能提供真实参考图片时，图片优先、文字用于补充。

```text
POSEWEAR RANDOM / SOLO — single-person premium photographic portrait.
Use exactly three visual reference roles:
(1) IDENTITY REFERENCE [人像图片或ID] controls adult facial identity, face structure, hairstyle, hair color, gaze and overall charisma;
(2) POSE REFERENCE [姿势图片或ID] strictly controls body pose, camera direction, torso tilt, shoulder and hip lines, arm positions, hands, knees, foot placement and weight bearing;
(3) OUTFIT REFERENCE [服装图片或ID] strictly controls garments, colors, layering, cut, drape, material, shoes, bags and accessories.

Blend all three roles into ONE adult human subject. Do not inherit unwanted clothes from the identity reference or unwanted faces from the pose reference. Never beautify by changing the prescribed action.

Scene chosen for the person's styling: [具体室内或户外场景]; lighting: [光线方向/色温/环境补光]; composition: [全身/半身/机位/头部和鞋履留白]. Appropriate architecture, natural object contact and coherent shadows.

Simulated Nikon Z8 professional full-frame photographic character with NIKKOR Z [50/85/105]mm lens, f/[2.2~4], realistic optical bokeh, accurate eye focus, detailed textiles, subtle hair strands, authentic pores and skin-tone micro-variation, natural highlight roll-off, understated cinematic color grading, high-resolution fine detail. Target 9:16 portrait. Exactly one person. Correct anatomy and fingers, footwear fully present when the pose requires it. No collage, no text, no watermark, no CG plastic skin.
```

**负面约束：** extra person, fused fingers, extra limbs, wrong pose, sitting instead of standing, missing shoes, random wardrobe changes, generic Gaussian-blurred cutout, plastic skin, duplicate accessories.

**记录**：原始输出像素、抽卡 ID/URL、哪些项目缺少实图比对。8K 为愿景而非原生像素保证。
