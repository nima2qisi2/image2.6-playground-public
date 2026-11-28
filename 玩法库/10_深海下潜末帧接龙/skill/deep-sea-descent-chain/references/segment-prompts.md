# 六段提示词原文｜深海 0–8000m 机舱第一视角案例

以下为定版案例（v1）实际使用的六段提示词（英文，图生视频）。第 1 段纯文本生成；第 2 段起每段同时喂上一段最后一帧作参考图，提示词首句即首帧锁定句。做新案例时保留骨架（视角与构图、唯一事件、声音段、负面句），只替换深度区间、分带、事件与声音元素。

每段共用骨架（机舱版）：

> first-person interior point of view inside the empty cabin of a deep-sea exploration submersible / camera fixed inside looking forward through the large round front viewport, no movement, no shaking, no rotation, no cut / cabin completely empty: NO people, no pilots, no hands / instrument panels with abstract unreadable graphics, absolutely no text, no letters, no numbers / WITH SOUND: [本段声音] / absolutely no human voice, no narration, no speech, no music / No text, no watermark, no logo

## Segment 1（0–200m · 阳光带）

> 10 seconds, 16:9, photorealistic, first-person interior point of view inside the empty cabin of a deep-sea exploration submersible, documentary style. Camera is fixed inside the cabin looking forward through the large round front viewport, camera position does not move, no shaking, no rotation, no cut inside the segment. The cabin is completely empty: NO people, no pilots, no hands, no human figures anywhere, only the curved titanium cabin wall, empty seats and glowing instrument panels with abstract unreadable graphics and absolutely no text, no letters, no numbers anywhere in the picture. Through the viewport, bright and cheerful: the submersible dives from the sunlit surface at 0 meters down to 200 meters over a colorful coral reef, warm golden sunlight rays through turquoise water, schools of tropical fish swirling past the glass, a sea turtle gliding gracefully across the viewport, colorful coral and sea fans below. WITH SOUND, audio rendered: cheerful bubbling water, gentle water rushing past the hull, soft sonar pings, low electronic hum, absolutely no human voice, no narration, no speech, no music. No text, no watermark, no logo in the picture.

## Segment 2（200–1000m · 暮光带）

> Use the reference image as the first frame, start with exactly the same empty cabin interior, same round viewport, same composition and light. [骨架同上] Through the viewport: descent through the twilight zone from 200 to 1000 meters, still beautiful but the light fading from turquoise to deep blue, the last god rays disappearing above, translucent jellyfish pulsing gently past the glass, a school of silvery fish scattering, the submersible headlights switching on toward the end, mood shifting from cheerful to quiet and mysterious. WITH SOUND: muffled water rushing, soft bubbles fading, gentle sonar pings, low electronic hum, no voice, no music.

## Segment 3（1000–2500m · 午夜带）

> [首帧锁定句＋骨架同上] Through the viewport: descent through the midnight zone from 1000 to 2500 meters, pitch black outside, only the headlight cone cutting through darkness, thick marine snow, tiny bioluminescent flashes, mood becoming dark, uneasy and tense; near the end an enormous slow shadow, far larger than the submersible, passes silently through the far edge of the light beam and vanishes into blackness. WITH SOUND: deep muffled pressure sounds, slow sonar pings, metallic hull creaks growing louder, a deep distant low rumble as the giant shadow passes, low electronic hum, no voice, no music.
>
> 注：本段巨影在成片中长成了巨鲸形（见案例偏差清单）。要保持"不可名状"，可在事件句追加 "an indistinct shapeless shadow with no recognizable animal form"。

## Segment 4（2500–4000m · 深渊峡谷）

> [首帧锁定句＋骨架同上] Through the viewport: descent from 2500 to 4000 meters through a dark abyssal canyon, rock walls on both sides, headlights sweeping black water; a giant squid with huge tentacles emerges from the darkness and passes very close across the viewport, one enormous eye staring in through the glass for a moment, then it slides away into the black, mood dangerous and tense. WITH SOUND: deep muffled water, tense slow sonar pings, loud metallic hull creaks and groans, a deep whoosh as the giant squid passes the glass, low electronic hum, no voice, no music.
>
> 注："passes very close" 是成片中乌贼贴近舱面的原因；v2 经验是把距离写死为窗外 2–3 米、并加 "never touching the glass, never filling the frame"。

## Segment 5（4000–6000m · 未知巨物）

> [首帧锁定句＋骨架同上] Through the viewport: descent from 4000 to 6000 meters in total darkness, headlights revealing only swirling particles; an unknown colossal deep-sea creature, far larger than the submersible and like nothing known, slowly circles in the darkness beyond the light, its body faintly glowing with rows of pale blue bioluminescent lights, its vast silhouette blocking the headlight beam as it passes in front, mood terrifying and dangerous. WITH SOUND: deep oppressive water pressure sounds, urgent faster sonar pings, loud metallic hull groans, a very deep slow creature rumble vibrating through the hull, low electronic hum, no voice, no music.

## Segment 6（6000–8000m · 海沟）

> [首帧锁定句＋骨架同上] Through the viewport: final descent from 6000 to 8000 meters into a hadal trench, pitch black and silent world, the colossal unknown creature's glowing lights fading away in the far distance behind, steep trench walls closing in, then the submersible levels out over the empty pale trench floor at 8000 meters, one small unknown glowing creature drifting far ahead in the darkness, mood eerie, tense and awe-filled. WITH SOUND: extremely deep muffled pressure sounds, very slow sparse sonar pings, faint metallic hull creaks, the distant creature rumble fading away, low electronic hum, no voice, no music.

## 艇外跟拍版 · 六段新版提示词模板（0–5000m 案例的写法）

与机舱版同为六段接龙，差别在视角：镜头在艇外伴飞，机位按段轮换。以下模板为本玩法自拟的新版措辞，做新案例时保留骨架、替换深度与事件即可。每段共用骨架（艇外版）：

> 10 seconds, 16:9, photorealistic underwater documentary footage of one single white deep-sea submersible. The camera travels alongside the submersible, holding one constant relative position for the whole segment, easing very slowly closer and never circling, never swinging to face it head-on, no shake, no roll, a single unbroken shot. The submersible keeps its shape, size and markings, it is the only vessel in the water, it moves steadily forward the entire time. Completely silent, no audio at all. No text, no captions, no watermark, no logo.

各段在骨架后接一句机位与事件（第 2 段起在骨架前加首帧锁定句 "Begin exactly from the reference frame, same scene, same light, continuing seamlessly."）：

| 段 | 机位与事件句 |
| --- | --- |
| 1（0–200m） | Camera position: behind and slightly above the submersible. It slips beneath the bright surface into the sunlit blue, coral reef and drifting schools of fish below, light rays slanting through the water. |
| 2（200–1000m） | Camera position: level with its left side. The blue deepens into twilight, the reef drops away, small glowing specks begin to appear in the gloom. |
| 3（1000–2500m） | Camera position: behind its right shoulder. Near-total darkness, its headlight cone filled with falling marine snow and faint bioluminescent flashes. |
| 4（2500–4000m） | Camera position: high behind it. A dark rocky canyon rises on both sides and it threads through the gorge, headlights sweeping the walls. |
| 5（4000–4800m） | Camera position: low at its side, close. Black hydrothermal smokers tower past, shimmering vent water and clouds of dark plume, a robotic arm folded against its hull. |
| 6（4800–5000m） | Camera position: high behind it. The canyon opens onto a vast pale abyssal plain, the submersible settles toward the sediment and slows to rest above the empty floor. |

该版全程静音（无音轨），深度 UI 未叠加；如需 UI，按机舱版同一套脚本后期叠加即可。
