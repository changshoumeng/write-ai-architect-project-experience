#!/usr/bin/env python3
"""Validate AI architect project-experience case documents."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


CASE_SECTION_PATTERNS = [
    ("项目介绍", re.compile(r"^一\s*[、,，]\s*项目介绍[:：]\s*$", re.MULTILINE)),
    ("核心技术", re.compile(r"^二\s*[、,，]\s*核心技术[:：]\s*$", re.MULTILINE)),
    (
        "关键职责与成果",
        re.compile(r"^三\s*[、,，]\s*关键职责与成果[:：]\s*$", re.MULTILINE),
    ),
]

CASE_LIMITS = {
    "项目介绍": (120, 200, 220),
    "核心技术": (350, 550, 650),
    "关键职责与成果": (250, 400, 500),
}

PLACEHOLDER_PATTERNS = [
    r"【(?:项目名称|项目时间|项目角色|目标用户/业务场景|核心痛点|核心工作|关键技术/方法|系统/智能体能力|可证明结果|不超过|[^】]*TODO[^】]*)】",
    r"\[TODO[:\]]",
    r"TODO",
]

OLD_PROJECT_TERMS = [
    "AIMA 组织架构智能体",
    "OfficeDrawIo",
    "PPT 回写",
    "xmlpng",
]

RISKY_METRIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:提升|降低|节省|减少|增长|准确率|召回率|成本|收入|用户|并发|QPS|ROI)"
    r"[^。\n，,；;]{0,20}\d+(?:\.\d+)?\s*(?:%|倍|人|万|ms|s|秒|分钟|小时|天|元|万元|条|个)"
)


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Path to Markdown output")
    parser.add_argument(
        "--mode",
        choices=["auto", "case", "resume-case"],
        default="auto",
        help="Validation mode. resume-case is kept as a compatibility alias for case.",
    )
    parser.add_argument(
        "--allow-old-project-terms",
        action="store_true",
        help="Allow known old-project terms when validating intentional legacy project text.",
    )
    parser.add_argument(
        "--allow-project-term",
        action="append",
        default=[],
        help="Allow a specific term that would otherwise be treated as contamination.",
    )
    return parser.parse_args()


def compact_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def case_sections(text: str) -> tuple[dict[str, str], list[str]]:
    matches: list[tuple[str, re.Match[str]]] = []
    errors: list[str] = []

    for name, pattern in CASE_SECTION_PATTERNS:
        match = pattern.search(text)
        if not match:
            errors.append(f"missing case section heading: {name}")
        else:
            matches.append((name, match))

    if errors:
        return {}, errors

    matches.sort(key=lambda item: item[1].start())
    expected_names = [name for name, _ in CASE_SECTION_PATTERNS]
    actual_names = [name for name, _ in matches]
    if actual_names != expected_names:
        errors.append("case section order does not match 一/二/三")
        return {}, errors

    sections: dict[str, str] = {}
    for index, (name, match) in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1][1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[body_start:body_end].strip()

    return sections, errors


def validate_common(
    text: str,
    errors: list[str],
    warnings: list[str],
    allow_old_terms: bool,
    allowed_terms: list[str],
) -> None:
    if not text.strip():
        errors.append("file is empty")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"unresolved placeholder pattern found: {pattern}")

    if not allow_old_terms:
        allowed = set(allowed_terms)
        found_terms = [term for term in OLD_PROJECT_TERMS if term in text and term not in allowed]
        if found_terms:
            errors.append("possible old-project contamination: " + ", ".join(found_terms))

    risky_metrics = sorted(set(RISKY_METRIC_PATTERN.findall(text)))
    if risky_metrics:
        warnings.append("check evidence for hard metrics: " + " | ".join(risky_metrics[:8]))

    if "客户高度认可" in text or "规模化推广" in text:
        warnings.append("customer recognition or scale rollout claims require strong evidence")


def validate_case(text: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    sections, section_errors = case_sections(text)
    errors.extend(section_errors)
    if errors:
        return ValidationResult(errors, warnings)

    for name, (target_min, target_max, hard_max) in CASE_LIMITS.items():
        length = compact_len(sections.get(name, ""))
        if length == 0:
            errors.append(f"empty case section: {name}")
        if length > hard_max:
            errors.append(f"{name} exceeds hard limit {hard_max} chars: {length}")
        elif length > target_max:
            warnings.append(f"{name} exceeds target {target_max} chars: {length}")
        if 0 < length < target_min:
            warnings.append(f"{name} is shorter than target {target_min} chars: {length}")
        warnings.append(f"{name} length: {length}/{target_min}-{target_max}")

    intro = sections["项目介绍"]
    sentence_count = len(re.findall(r"[。！？!?]", intro))
    if sentence_count > 3:
        warnings.append("项目介绍 should usually stay within two or three sentences")
    intro_compact = re.sub(r"\s+", "", intro)
    if not any(term in intro_compact for term in ["改造", "流程", "场景", "痛点", "链路"]):
        warnings.append("项目介绍 should clarify business process, scenario, pain point, or transformed workflow")

    core = re.sub(r"\s+", "", sections["核心技术"]).lower()
    required_core_terms = [
        ("技术栈", "技术栈"),
        ("Agent架构设计", "agent架构设计"),
        ("AI 工程化", "ai工程化"),
    ]
    for label, needle in required_core_terms:
        if needle not in core:
            errors.append(f"核心技术 missing required dimension: {label}")
    task_flow_terms = ["入口", "任务流", "工作流", "链路", "调用", "回写", "交付", "状态"]
    if not any(term in core for term in task_flow_terms):
        warnings.append("核心技术 should expose user-entry-to-result task flow or system chain")
    harness_terms = ["harness", "prompt", "schema", "trace", "评测", "重试", "回退", "guardrails"]
    if not any(term in core for term in harness_terms):
        errors.append("核心技术 missing AI 工程化 details: Prompt/Schema/Trace/评测/重试/回退")
    if "集成" not in core and "嵌入" not in core and "连接" not in core:
        errors.append("核心技术 missing AI 工程化 details: 集成/嵌入/连接")
    if "观测" not in core and "观察" not in core and "trace" not in core and "日志" not in core:
        errors.append("核心技术 missing AI 工程化 details: 观测/Trace/日志")
    performance_terms = [
        "性能",
        "缓存",
        "cache",
        "cached",
        "token",
        "延迟",
        "首屏",
        "响应",
        "流式",
        "压缩",
        "quota",
        "配额",
        "成本",
        "降本",
        "提效",
        "频次",
        "埋点",
        "usage",
        "value",
    ]
    if not any(term in core for term in performance_terms):
        warnings.append("consider adding AI 工程化 performance/cost/value evidence if project facts support it")

    duties = re.sub(r"\s+", "", sections["关键职责与成果"])
    required_duty_terms = ["产品定义", "方案设计", "研发交付"]
    for term in required_duty_terms:
        if term not in duties:
            errors.append(f"关键职责与成果 missing required dimension: {term}")
    if not any(term in duties for term in ["我", "负责", "主导", "参与", "推动", "协同"]):
        warnings.append("关键职责与成果 should make personal responsibility boundary explicit")

    mechanical_patterns = [
        r"通过[^。；;\n]{0,30}基于[^。；;\n]{0,30}实现",
        r"(赋能|打造|全面提升|显著优化)",
    ]
    for pattern in mechanical_patterns:
        if re.search(pattern, text):
            warnings.append(f"check for mechanical or promotional wording: {pattern}")
    if text.count("通过") >= 4:
        warnings.append("check repeated 通过-style sentence pattern; prose may feel mechanical")

    return ValidationResult(errors, warnings)


def main() -> int:
    args = parse_args()
    target = args.file

    if not target.exists():
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 2

    text = target.read_text(encoding="utf-8")
    common_errors: list[str] = []
    common_warnings: list[str] = []
    validate_common(
        text,
        common_errors,
        common_warnings,
        args.allow_old_project_terms,
        args.allow_project_term,
    )

    result = validate_case(text)
    errors = common_errors + result.errors
    warnings = common_warnings + result.warnings

    mode = "case" if args.mode in {"auto", "resume-case", "case"} else args.mode
    if errors:
        print(f"Validation failed ({mode}):")
        for item in errors:
            print(f"- ERROR: {item}")
        for item in warnings:
            print(f"- WARN: {item}")
        return 1

    print(f"Validation passed ({mode}).")
    for item in warnings:
        print(f"- WARN: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
