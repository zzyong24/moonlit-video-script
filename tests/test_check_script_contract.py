from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


def _load_checker():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_script_contract.py"
    spec = importlib.util.spec_from_file_location("check_script_contract", script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


checker = _load_checker()

VALID_TALKING_HEAD = """# AI 开发脚手架：让每次对话顺着同一条任务接力 · 视频脚本

- 作品：`W-20261118-001`
- status：`draft`
- production_mode：`talking_head_broll`
- 目标平台：抖音、视频号、B站、小红书
- 画幅：`16:9`
- 预估时长：约 2 分 10 秒
- script 阶段三审：`pending（初稿不强审）`

## 章节推进

1. `P01｜换窗口就断片：代码写出来了事情没完`
2. `P02｜读取清单与范围边界：开工前只喂本步材料`
3. `P03｜红绿日志与回读：对照最初目标交工`

## 镜次表

| 镜号与章节 | 预估时段 | 对应口播锚点 | 视觉主语与可观察变化 | 信息职责与人物状态 | 字幕重点 | 素材来源与状态 |
|---|---|---|---|---|---|---|
| S01 · P01 | 0:00–0:15 | 第1段 | 真人直视提出换窗口重讲进度的处境；0:07 切待办文件定位到 T-1450 行 | 建立相关性｜全屏真人→全屏证据（隐藏人物） | 换窗口怎么接着做 | 需真人实录；BACKLOG 录屏 `planned` |
| S02 · P02 | 0:15–0:45 | 第2段 | 单一机制：任务请求进入 context-plan → 高亮本次允许改的 2 个文件，采集与重试文件锁灰 | 解释机制｜全屏代码动画＋左下圆窗头像 | 读什么／不能碰什么 | 状态动画 `planned`（不用三张文字列表卡代替） |
| S03 · P03 | 0:45–1:10 | 第3段 | 打开历史测试日志：3 failed 聚焦到 25 passed，再切回读报告错误提示变化 | 举证结果｜全屏证据（隐藏人物） | 3失败→25通过 | 历史日志已核；录屏 `planned` |
| S04 · P03 | 1:10–1:15 | 末句 | 复用已确认默认片尾原视频与原录音，中英字幕同窗 | 片尾收束｜原素材全屏 | 关注我，一起用 AI 提效 | `maintenance/video-cta-default.json` v01 |

## 口播净稿

让 AI 加个功能，代码很快就出来了。可一换对话窗口，它又不知道项目做到了哪一步。

这套开源脚手架先用 context-plan 列出当前步骤该读的文件路径和不能碰的边界，让 AI 实际读完再动手。

改完之后看历史日志，二十五个检查全部通过，回读报告确认错误引导已经修好。关注我，一起用 AI 提效，把想法做成能卖的东西。
"""

VALID_HTML_PRESENTATION = """# 开源开发脚手架运行链路 · 演示讲解稿

- 作品：`W-20261118-002`
- status：`confirmed`
- production_mode：`html_presentation`
- 画幅：`16:9`
- script 阶段三审：`passed（见 production/publish-review/v01/receipt.json，guoshen --require-chain-version 2）`

## 分页职责与现场动作表

| 页编号 | 页面具象标题 | 单一解释任务与可见逻辑结构 | 现场动作提示（不朗读） | 素材与来源状态 |
|---|---|---|---|---|
| S01 | 需求、实现和验收怎样接起来 | 顶层五阶段流程图与右侧人工决策位 | 先指顶层链路，再停在验证节点 | 原生 SVG 关系图，已核架构文档 |

## 独立讲解净稿

先看页面最上方这条链路。每次接手新任务前，先把要解决的问题、允许改的文件和检查标准写进项目记录，再开始写代码。
"""

BROKEN_LEGACY_SCRIPT = """# 测试脚本

> production_mode：[ ] html_explainer [ ] talking_head_broll
> 画幅：9:16 / 16:9
> status: confirmed

## 章节推进

1. 总结：收尾

## 镜次表

| 时间 | 旁白 | 画面主语与变化 | 素材来源 |
|---|---|---|---|
| 0:00–0:08 | 开头 | 展示相关代码界面 | 录屏 |
| 0:08–0:16 | 中段 | 右下角弹出三个清单卡片 | AI图 |

## 口播净稿

### 总结

开篇 · 文章的核心问题就是这样。（切录屏）大家可以参考一下，效果仅供参考。
"""


class CheckScriptContractTests(unittest.TestCase):
    def test_valid_talking_head_passes_in_spaced_temp_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="moonlit script test ") as tmp:
            p = Path(tmp) / "11180930-开发脚手架-视频脚本.md"
            p.write_text(VALID_TALKING_HEAD, encoding="utf-8")
            report = checker.check_markdown(p)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["errors"], 0)
            self.assertEqual(report["warnings"], 0)
            self.assertEqual(report["production_mode"], "talking_head_broll")

    def test_valid_html_presentation_confirmed_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="moonlit ppt test ") as tmp:
            p = Path(tmp) / "11181000-脚手架演示-视频脚本.md"
            p.write_text(VALID_HTML_PRESENTATION, encoding="utf-8")
            report = checker.check_markdown(p)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["production_mode"], "html_presentation")

    def test_manual_mode_rejects_tts_contamination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad-manual.md"
            p.write_text(
                VALID_HTML_PRESENTATION + "\n配音送入 TTS 并使用 MiniMax 合成整稿。\n",
                encoding="utf-8",
            )
            report = checker.check_markdown(p)
            codes = {f["code"] for f in report["findings"]}
            self.assertIn("manual_mode_tts_contamination", codes)
            self.assertFalse(report["passed"])

    def test_broken_legacy_script_catches_all_contract_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "legacy.md"
            p.write_text(BROKEN_LEGACY_SCRIPT, encoding="utf-8")
            report = checker.check_markdown(p)
            self.assertFalse(report["passed"])
            codes = {f["code"] for f in report["findings"]}
            self.assertIn("unselected_production_mode", codes)
            self.assertIn("unselected_aspect_ratio", codes)
            self.assertIn("confirmed_missing_script_review", codes)
            self.assertIn("vague_chapter_title", codes)
            self.assertIn("vague_visual_duty", codes)
            self.assertIn("static_list_card_visual", codes)
            self.assertIn("missing_asset_status", codes)
            self.assertIn("heading_in_net_draft", codes)
            self.assertIn("meta_language_leak", codes)
            self.assertIn("stage_direction_in_net_draft", codes)
            self.assertIn("hedging_phrase_check", codes)


    def test_draft_with_parenthetical_confirmed_note_and_checkbox_mode(self) -> None:
        doc = VALID_TALKING_HEAD.replace(
            "- status：`draft`",
            "- status：`draft`（待确认后改为 `confirmed` 并跑 guoshen）",
        ).replace(
            "- production_mode：`talking_head_broll`",
            "- production_mode：[x] talking_head_broll [ ] html_explainer",
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft-note.md"
            p.write_text(doc, encoding="utf-8")
            report = checker.check_markdown(p)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["production_mode"], "talking_head_broll")


if __name__ == "__main__":
    unittest.main()
