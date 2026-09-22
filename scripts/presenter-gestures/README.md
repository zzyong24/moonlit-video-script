# 可复用主持人动作组装工具

Python 3 + ffmpeg/ffprobe，无云端调用和自动扣费。内容资产与 catalog 保留在作品 production，工具源码只在本仓库。

```bash
python3 gesture_library.py plan /absolute/catalog.json --sequence explain-right compare-two --duration 29.507 --out /tmp/plan.json
python3 gesture_library.py render-base /tmp/plan.json --out /tmp/base.mp4
python3 gesture_library.py render-review /tmp/plan.json --video /absolute/lipsynced.mp4 --audio /absolute/original.wav --covers /absolute/covers.json --out /tmp/review.mp4
```

`plan` 的范围以统一 fps 的帧号计，end exclusive。时长向上取整到视频帧，不改变主音频。`render-base` 生成诊断/口型输入，不代表衔接通过验收。`render-review` 必须用真实不透明内容素材绑定每个待覆盖接缝，按音频时长导出；音频编码为 AAC，但不做变速、滤镜或重采样。输出路径存在时拒绝覆盖。

新增资产：登记来源、完整动作区间、进出姿态、角色/服装/机位、语义标签、候选/通过/禁用状态、可否循环。每个有向连接单独验收，不能由 A→B 推断 B→A。必须有动态验收证据才可改为 direct + approved + reviewEvidence。

已知限制：不会合成物理连续的手势过渡，不会根据文字猜动作，不会自动评估语义匹配。未验收接缝的安全降级是隐藏人物并展示有信息职责的素材；不可用人脸/手部叠化冒充修复。
