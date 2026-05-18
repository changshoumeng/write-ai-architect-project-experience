#!/usr/bin/env python3
"""Validate AI architect project-experience final Markdown structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "# AI 技术架构师项目经历：",
    "## 项目元信息",
    "## 一句话价值主张",
    "## 项目背景与业务痛点",
    "## 我的角色与职责边界",
    "## 核心技术",
    "## 简历主版本",
    "## 简历精简版",
    "## 简历要点版",
    "## 最终自检",
]

ALLOWED_H2 = {section for section in REQUIRED_SECTIONS if section.startswith("## ")}
REQUIRED_META_FIELDS = ["- 项目名称：", "- 项目时间：", "- 项目角色："]
FORBIDDEN_META_FIELDS = ["- 项目类型：", "- 客户/行业："]

PLACEHOLDER_PATTERNS = [
    r"【(?:项目名称|项目时间|项目角色|目标用户/业务场景|核心痛点|核心工作|关键技术/方法|系统/智能体能力|可证明结果|[^】]*TODO[^】]*)】",
    r"\[TODO[:\]]",
    r"TODO",
]

OLD_PROJECT_TERMS = [
    "AIMA 组织架构智能体",
    "OfficeDrawIo",
    "next-ai-draw-io",
    "Draw.io",
    "PPT 回写",
    "xmlpng",
]

RISKY_METRIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:提升|降低|节省|减少|增长|准确率|召回率|成本|收入|用户|并发|QPS|ROI)[^。\n，,；;]{0,20}\d+(?:\.\d+)?\s*(?:%|倍|人|万|ms|s|秒|分钟|小时|天|元|万元|条|个)"
)
VENDOR_SCORE_PATTERN = re.compile(r"乙方专业交付视角评分：\s*(\d{1,3})\s*/\s*100")
BUYER_SCORE_PATTERN = re.compile(r"甲方\s*HR/面试官\s*SKAOs\s*评分：\s*(\d{1,3})\s*/\s*100")
CHECKED_LOW_SCORE_PATTERN = re.compile(r"- \[x\].*评分：\s*(\d{1,3})\s*/\s*100")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Path to 项目经历-最终.md")
    parser.add_argument(
        "--allow-old-project-terms",
        action="store_true",
        help="Allow common pm01 Office/Draw.io terms when validating that project intentionally.",
    )
    return parser.parse_args()


def section_body(text: str, section: str) -> str:
    start = text.find(section)
    if start < 0:
        return ""
    body_start = start + len(section)
    next_heading = text.find("\n## ", body_start)
    if next_heading < 0:
        return text[body_start:].strip()
    return text[body_start:next_heading].strip()


def extract_score(pattern: re.Pattern[str], text: str, label: str, errors: list[str]) -> int | None:
    match = pattern.search(text)
    if not match:
        errors.append(f"missing score in 最终自检: {label}")
        return None

    score = int(match.group(1))
    if score > 100:
        errors.append(f"score over 100 for {label}: {score}")
    if score < 95:
        errors.append(f"score below required 95 for {label}: {score}")
    return score


def main() -> int:
    args = parse_args()
    target = args.file

    if not target.exists():
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 2

    text = target.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("file is empty")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section: {section}")
        elif section.startswith("## ") and not section_body(text, section):
            errors.append(f"empty required section: {section}")

    actual_h2 = re.findall(r"^## .+$", text, flags=re.MULTILINE)
    extra_h2 = [heading for heading in actual_h2 if heading not in ALLOWED_H2]
    if extra_h2:
        errors.append("unexpected H2 section(s): " + ", ".join(extra_h2))

    expected_h2_order = [section for section in REQUIRED_SECTIONS if section.startswith("## ")]
    if actual_h2 != expected_h2_order:
        errors.append("H2 section order or set does not exactly match required structure")

    meta = section_body(text, "## 项目元信息")
    for field in REQUIRED_META_FIELDS:
        if field not in meta:
            errors.append(f"missing project metadata field: {field}")
    for field in FORBIDDEN_META_FIELDS:
        if field in meta:
            errors.append(f"forbidden project metadata field: {field}")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"unresolved placeholder pattern found: {pattern}")

    if not args.allow_old_project_terms:
        found_terms = [term for term in OLD_PROJECT_TERMS if term in text]
        if found_terms:
            errors.append("possible old-project contamination: " + ", ".join(found_terms))

    risky_metrics = sorted(set(RISKY_METRIC_PATTERN.findall(text)))
    if risky_metrics:
        warnings.append("check evidence for hard metrics: " + " | ".join(risky_metrics[:8]))

    if "客户高度认可" in text or "规模化推广" in text:
        warnings.append("customer recognition or scale rollout claims require strong evidence")

    final_check = section_body(text, "## 最终自检")
    extract_score(VENDOR_SCORE_PATTERN, final_check, "乙方专业交付视角评分", errors)
    extract_score(BUYER_SCORE_PATTERN, final_check, "甲方 HR/面试官 SKAOs 评分", errors)

    if "证据边界" not in final_check and "证据来源" not in final_check:
        errors.append("最终自检 must include evidence boundary or evidence source note")

    if "JD 匹配" not in final_check and "岗位匹配" not in final_check:
        errors.append("最终自检 must include JD match or target-role match note")

    checked_low_scores = [int(score) for score in CHECKED_LOW_SCORE_PATTERN.findall(final_check) if int(score) < 95]
    if checked_low_scores:
        errors.append("checked score below 95 found in 最终自检: " + ", ".join(map(str, checked_low_scores)))

    if "__/100" in final_check:
        errors.append("unfilled score placeholder found in 最终自检")

    if errors:
        print("Validation failed:")
        for item in errors:
            print(f"- ERROR: {item}")
        for item in warnings:
            print(f"- WARN: {item}")
        return 1

    print("Validation passed.")
    for item in warnings:
        print(f"- WARN: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
