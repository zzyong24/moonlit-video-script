#!/usr/bin/env python3
"""Deterministic structure and contract checker for moonlit-video-script outputs.

Checks explicit production_mode routing, draft/confirmed review gate linkage,
concrete chapter naming, net-draft purity (no stage directions or internal meta-words),
and storyboard executability (no vague 'show related screen' or static list-card patterns).
Not a substitute for semantic review, guoshen risk review, or user approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

VALID_MODES = {
    "talking_head_broll",
    "html_explainer",
    "avatar_explainer",
    "html_presentation",
    "excalidraw_explainer",
}
MANUAL_MODES = {"html_presentation", "excalidraw_explainer"}

VAGUE_CHAPTER_TITLES = {
    "开场",
    "引言",
    "前言",
    "背景",
    "正文",
    "过渡",
    "行动",
    "总结",
    "收尾",
    "结尾",
    "收束",
    "概述",
    "小结",
    "核心观点",
    "痛点钩子",
    "agent时代",
    "ai时代",
}

META_LEAK_PHRASES = (
    "文章主线",
    "母稿案例",
    "开篇 · 文章的核心问题",
    "据母稿绘制",
    "对照与实践收束",
    "文章的视觉展开",
)

HEDGING_PHRASES = (
    "仅供参考",
    "以实际为准",
    "不能保证",
    "这只能证明",
    "待核验",
)

VAGUE_VISUAL_PATTERNS = re.compile(
    r"展示[^，。；|]{0,16}相关(?:画面|界面|代码|内容|素材|截图|操作|配置)|配相关(?:图片|画面|素材)|相关(?:画面|素材)展示|展示操作过程"
)

STATIC_CARD_PATTERNS = re.compile(
    r"(?:弹出|打出|翻出)[一二三四五六七八九十\d]+(?:个|张|栏|条)?(?:清单|卡片|问题|要点|文字卡)|"
    r"[一二三四五\d]+(?:栏|张)(?:内容)?卡片依次|"
    r"静态(?:列表卡|PPT\s*卡|文字卡)|逐行淡入(?:清单|卡片)|文字卡片轮播"
)

TEMPLATE_PLACEHOLDERS = (
    "[一个主视觉]",
    "[痛点 + 收益]",
    "[关键词]",
    "HTML/截图/录屏/AI 图/真人",
)

STAGE_DIRECTION_RE = re.compile(
    r"（[^）]{0,20}(?:切录屏|切画面|停顿|弹出|特写|闪回|画面切|镜头)[^）]*）|"
    r"\([^)]{0,20}(?:切录屏|切画面|停顿|特写|闪回)[^)]*\)|"
    r"\[(?:停顿|切镜|画面|痛点\s*\+\s*收益)[^\]]*\]|"
    r"【(?:切镜|画面|停顿|旁白提示)[^】]*】"
)

BARE_ASSET_WORDS = {
    "录屏",
    "截图",
    "ai图",
    "ai 图",
    "动画",
    "动效",
    "真人",
    "html",
    "配图",
    "素材",
    "-",
    "—",
    "待定",
}

NET_DRAFT_HEADINGS = (
    "口播净稿",
    "逐句旁白",
    "ai旁白稿",
    "ai 旁白稿",
    "独立讲解净稿",
    "讲解净稿",
)


def _normalize_title_token(raw: str) -> str:
    text = raw.strip().strip("`*_ ")
    # Strip leading numbering like "1. ", "P01｜", "第1节："
    text = re.sub(r"^(?:第[一二三四五六七八九十\d]+[节章部分]|[PSN]\d+[a-z]?|\d+)[\s.、｜|:：-]+", "", text, flags=re.I)
    # Strip trailing time range like "｜0:00–0:12"
    text = re.sub(r"\s*[｜|]\s*\d+:\d+.*$", "", text)
    text = re.sub(r"[\s·—\-_:：｜|]+", "", text).lower()
    return text


def _split_sections(lines: list[str]) -> list[tuple[int, str, list[tuple[int, str]]]]:
    sections: list[tuple[int, str, list[tuple[int, str]]]] = []
    cur_line = 1
    cur_heading = "__preamble__"
    cur_body: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, 1):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            sections.append((cur_line, cur_heading, cur_body))
            cur_line = idx
            cur_heading = m.group(1).strip()
            cur_body = []
        else:
            cur_body.append((idx, line))
    sections.append((cur_line, cur_heading, cur_body))
    return sections


def check_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[dict] = []

    def add(severity: str, code: str, line: int, detail: str) -> None:
        findings.append(
            {
                "severity": severity,
                "code": code,
                "line": line,
                "detail": detail,
            }
        )

    # 1. Check production_mode
    mode_matches: list[tuple[int, str]] = []
    for idx, line in enumerate(lines[:60], 1):
        m = re.search(r"production_mode\s*(?:[:：=])\s*(.+)$", line)
        if m:
            mode_matches.append((idx, m.group(1).strip()))

    selected_mode: str | None = None
    if not mode_matches:
        add("error", "missing_production_mode", 1, "未声明 production_mode；须从 5 类合法模式中显式选定唯一值")
    else:
        line_no, raw_val = mode_matches[0]
        checked = re.findall(r"\[[xX]\]\s*`?([a-z_]+)`?", raw_val)
        if checked:
            if len(checked) == 1 and checked[0] in VALID_MODES:
                selected_mode = checked[0]
            else:
                add("error", "invalid_production_mode", line_no, f"勾选了多个或非法的 production_mode：{raw_val}")
        elif (
            "[ ]" in raw_val
            or ("|" in raw_val and sum(m in raw_val for m in VALID_MODES) > 1)
            or ("或" in raw_val and sum(m in raw_val for m in VALID_MODES) > 1)
            or raw_val.startswith("待定")
        ):
            add("error", "unselected_production_mode", line_no, f"production_mode 尚未锁定唯一值：{raw_val}")
        else:
            token_match = re.search(r"`?([a-z][a-z0-9_]+)`?", raw_val)
            candidates = [token_match.group(1)] if token_match else []
            if len(candidates) != 1 or candidates[0] not in VALID_MODES:
                add(
                    "error",
                    "invalid_production_mode",
                    line_no,
                    f"非法或模糊的 production_mode：{raw_val}；允许值：{', '.join(sorted(VALID_MODES))}",
                )
            else:
                selected_mode = candidates[0]

    # 2. Check status & script review gate
    status_line = 0
    status_val = ""
    for idx, line in enumerate(lines[:50], 1):
        m = re.search(r"(?:^[-*>#\s]*)(?:status|内部状态|状态)\s*[:：]\s*(.+)$", line, flags=re.I)
        if m:
            status_line = idx
            status_val = m.group(1).strip().lower()
            break

    primary_status = re.split(r"[（(；;—|]", status_val, maxsplit=1)[0].strip(" `*_") if status_val else ""
    if not primary_status:
        add("warning", "missing_status", 1, "未标注脚本状态（建议写明 status: draft 或 confirmed）")
    elif primary_status in ("confirmed", "已确认"):
        has_review_ref = bool(
            re.search(r"(?:guoshen|publish_review_gate|publish-review|script\s*阶段|script审核|--require-chain-version\s+2)", text, re.I)
        )
        pending_review = bool(
            re.search(r"script\s*(?:阶段)?(?:三审|审核)\s*[:：]\s*`?(?:pending|未审|待审)", text, re.I)
        )
        if not has_review_ref or pending_review:
            add(
                "error",
                "confirmed_missing_script_review",
                status_line,
                "文案已标 confirmed，移交制作前须执行 guoshen script 阶段审核（--require-chain-version 2）并登记有效状态",
            )

    # 3. Aspect ratio check
    for idx, line in enumerate(lines[:50], 1):
        m = re.search(r"(?:画幅|比例|aspect)\s*[:：]\s*(.+)$", line, flags=re.I)
        if m:
            val = m.group(1).strip()
            if "9:16 / 16:9" in val or "16:9 / 9:16" in val:
                add("error", "unselected_aspect_ratio", idx, f"画幅仍为未选择的模板占位：{val}")
            elif ("9:16" in val or "竖屏" in val or "竖版" in val) and "16:9" not in val:
                if not re.search(r"(?:指定|要求|源素材|竖屏源|槽位|明确)", val):
                    add("warning", "non_default_aspect_ratio", idx, "默认画幅为 16:9 横屏；选 9:16 请注明用户明确要求或竖屏源素材依据")
            break

    # 4. Mode cross-contamination check
    if selected_mode in MANUAL_MODES:
        for idx, line in enumerate(lines, 1):
            if re.search(r"(?:MiniMax|MoonlitZhu|送入\s*TTS|合成整稿|供应商\s*SRT)", line, flags=re.I):
                if not re.search(r"(?:不|无需|禁止|免)", line):
                    add("error", "manual_mode_tts_contamination", idx, f"{selected_mode} 为手动演示/自由画布模式，不应混入自动 TTS 配音或供应商 SRT 要求")

    sections = _split_sections(lines)

    # 5. Chapter concrete check & Net-draft purity check
    found_net_draft = False
    found_storyboard = False

    for sec_line, sec_title, sec_body in sections:
        norm_sec = sec_title.strip().lower()

        # Check chapter progression list
        if any(k in norm_sec for k in ("章节", "目录")):
            for lno, ltxt in sec_body:
                m = re.match(r"^\s*(?:\d+\.|[-*])\s*(.+?)(?:[:：]\s*.*)?$", ltxt)
                if m:
                    cand = m.group(1).split("：")[0].split(":")[0]
                    if _normalize_title_token(cand) in VAGUE_CHAPTER_TITLES:
                        add("error", "vague_chapter_title", lno, f"章节名过宽泛（{cand.strip()}），须点明具体对象＋判断或动作")

        # Check subheadings anywhere for vague titles or meta leaks
        for lno, ltxt in sec_body:
            sub = re.match(r"^###\s+(.+?)\s*$", ltxt)
            if sub:
                raw_sub = sub.group(1)
                if _normalize_title_token(raw_sub) in VAGUE_CHAPTER_TITLES:
                    add("error", "vague_chapter_title", lno, f"小节/章节名过宽泛（{raw_sub}），须点明具体对象＋判断或动作")
                for phrase in META_LEAK_PHRASES:
                    if phrase in raw_sub:
                        add("error", "meta_language_leak", lno, f"章节标题包含内部制作元话术：{phrase}")

        # Net-draft section checks
        is_pure_net_draft = any(k in norm_sec.replace(" ", "") for k in [h.replace(" ", "") for h in NET_DRAFT_HEADINGS])
        is_legacy_spoken = any(k in norm_sec for k in ("完整口播", "口播初稿", "口播正文"))
        if is_pure_net_draft or is_legacy_spoken:
            found_net_draft = True
            non_empty_spoken = 0
            for lno, ltxt in sec_body:
                stripped = ltxt.strip()
                if not stripped or stripped == "---" or stripped == "***":
                    continue
                if is_pure_net_draft and re.match(r"^#{2,4}\s+", stripped):
                    add("error", "heading_in_net_draft", lno, "纯朗读净稿区块内混入了 Markdown 章节标题，标题须移出净稿以防误送 TTS")
                    continue
                if is_pure_net_draft and re.match(r"^\*\*(?:画面|镜头|节奏|动作|边界|提示)\*\*\s*[:：]", stripped):
                    add("error", "non_spoken_in_net_draft", lno, f"纯朗读净稿内混入导演/分镜字段：{stripped[:24]}")
                    continue
                if stripped.startswith(">") and is_pure_net_draft:
                    # Allow plain text; strip blockquote marker for content check
                    stripped = stripped.lstrip("> ").strip()
                non_empty_spoken += 1

                for phrase in META_LEAK_PHRASES:
                    if phrase in stripped:
                        add("error", "meta_language_leak", lno, f"朗读稿出现内部制作编排词：{phrase}")
                if STAGE_DIRECTION_RE.search(stripped):
                    add("error", "stage_direction_in_net_draft", lno, f"朗读稿混入舞台/切镜/停顿括号提示：{stripped[:36]}")
                for hedge in HEDGING_PHRASES:
                    if hedge in stripped:
                        add("warning", "hedging_phrase_check", lno, f"朗读稿含“{hedge}”，请确认系作者原话；禁止助手自行添加规避性话术")

            if non_empty_spoken == 0:
                add("error", "empty_spoken_section", sec_line, f"“{sec_title}”区块为空")

        # 6. Storyboard / Slide table checks
        if any(k in norm_sec for k in ("镜次", "分镜", "镜头表", "分页", "分区")):
            table_rows: list[tuple[int, list[str]]] = []
            for lno, ltxt in sec_body:
                s = ltxt.strip()
                if s.startswith("|") and s.endswith("|"):
                    cells = [c.strip() for c in s.strip("|").split("|")]
                    table_rows.append((lno, cells))
            if len(table_rows) >= 3:
                found_storyboard = True
                headers = [h.lower() for h in table_rows[0][1]]
                visual_idx = next(
                    (i for i, h in enumerate(headers) if any(k in h for k in ("画面", "视觉", "解释任务", "可见"))),
                    None,
                )
                asset_idx = next(
                    (i for i, h in enumerate(headers) if any(k in h for k in ("素材", "来源", "状态"))),
                    None,
                )
                chap_idx = next(
                    (i for i, h in enumerate(headers) if any(k in h for k in ("章节", "页面", "标题", "段落"))),
                    None,
                )

                for r_lno, cells in table_rows[2:]:
                    row_joined = " | ".join(cells)
                    if all(not c or c in ("…", "...") for c in cells):
                        continue
                    for ph in TEMPLATE_PLACEHOLDERS:
                        if ph in row_joined:
                            add("error", "unfilled_template_placeholder", r_lno, f"分镜表残留未填写的模板占位符：{ph}")

                    if chap_idx is not None and chap_idx < len(cells):
                        c_tok = _normalize_title_token(cells[chap_idx])
                        if c_tok in VAGUE_CHAPTER_TITLES:
                            add("error", "vague_chapter_title", r_lno, f"分镜章节/段落名过宽泛：{cells[chap_idx]}")

                    if visual_idx is not None and visual_idx < len(cells):
                        vis = cells[visual_idx]
                        if not vis:
                            add("error", "empty_visual_duty", r_lno, "分镜画面/视觉职责列为空")
                        else:
                            if VAGUE_VISUAL_PATTERNS.search(vis):
                                add("error", "vague_visual_duty", r_lno, f"分镜描述过于空泛（{vis[:28]}），须写明具体界面局部或状态变化")
                            if STATIC_CARD_PATTERNS.search(vis) and not re.search(r"(?:不|禁止|避免)(?:用|做|使用)?", vis):
                                add(
                                    "error",
                                    "static_list_card_visual",
                                    r_lno,
                                    f"分镜疑似把口播拆成静态等权文字卡充当主画面（{vis[:30]}）；请改为真实证据聚焦或物件状态变化",
                                )

                    if asset_idx is not None and asset_idx < len(cells) and selected_mode not in MANUAL_MODES:
                        ast = cells[asset_idx]
                        if not ast or ast.strip().lower() in BARE_ASSET_WORDS:
                            add(
                                "error",
                                "missing_asset_status",
                                r_lno,
                                f"素材来源与状态列过于笼统（“{ast}”）；须注明已有文件/配置引用或 planned/待采集/待实录状态",
                            )

    if not found_net_draft:
        add("error", "missing_spoken_section", 1, "未找到独立的口播/旁白/讲解净稿二级章节（如 `## 口播净稿` 或 `## 独立讲解净稿`）")
    if not found_storyboard:
        add("error", "missing_storyboard_table", 1, "未找到可执行镜次表或分页/分区职责表（如 `## 镜次表` 或 `## 分页 / 分区职责与现场动作表`）")

    error_count = sum(1 for f in findings if f["severity"] == "error")
    warning_count = sum(1 for f in findings if f["severity"] == "warning")
    return {
        "schema_version": 1,
        "file": str(path),
        "production_mode": selected_mode,
        "errors": error_count,
        "warnings": warning_count,
        "passed": error_count == 0,
        "findings": findings,
        "note": "确定性结构与契约检查；不替代作者原意审读、guoshen风险三审或用户认可",
    }


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 10):
        raise SystemExit("需要 Python 3.10+")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script_file", type=Path, help="待检查的视频脚本或演示讲解稿 Markdown 路径")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    if not args.script_file.is_file():
        parser.error(f"文件不存在：{args.script_file}")

    report = check_markdown(args.script_file)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status_label = "PASSED" if report["passed"] else "FAILED"
        print(
            f"[{status_label}] mode={report['production_mode'] or 'unknown'} "
            f"errors={report['errors']} warnings={report['warnings']} — {report['note']}"
        )
        for item in report["findings"]:
            print(f"  {item['severity'].upper()} {item['code']} L{item['line']}: {item['detail']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
