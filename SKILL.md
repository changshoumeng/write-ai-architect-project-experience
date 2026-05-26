---
name: write-ai-architect-project-experience
description: "根据 JD、项目描述或已有项目经历，生成、审查并重写符合 project-experience-case-template.md 的 AI 技术架构师项目经历文档。Use when Codex needs to: (1) write a resume-ready AI architect / AI Agent / RAG / LLM project experience from a JD plus project description, or (2) score an existing project experience out of 100, identify issues, and rewrite it into a clear HR/interviewer-ready project experience."
---

# Write AI Architect Project Experience

## Purpose

Use this skill for exactly two jobs:

1. **Generate Case**: Given a target JD and project description, write a project-experience document that conforms to `assets/project-experience-case-template.md` and is ready for HR screening and technical interview review.
2. **Review And Rewrite Case**: Given an existing project-experience document, score it out of 100, identify concrete issues and revision advice, then rewrite it into a document that conforms to `assets/project-experience-case-template.md`.

The final rewritten or generated project experience must be evidence-bound, readable, role-aware, and understandable at a glance by HR and interviewers.

## Resource Boundaries

- `SKILL.md` defines the two workflows and when to ask for missing input.
- `assets/project-experience-case-template.md` defines the output shape only. Treat it as a template, not a system prompt.
- `references/execution-prompt.md` defines writing and review procedure.
- `references/input-contract.md` defines required inputs and evidence grading.
- `references/quality-gates.md` defines the 100-point review rubric and rewrite gates.
- `scripts/validate_project_experience.py` checks deterministic structure, required dimensions, risky claims, and length ranges.

## Workflows

### 1. Generate Case

Use when the user provides a JD and project description, or asks to create a project experience for投递/简历/HR/面试官.

Steps:

1. Read the JD and extract target-role abilities: Skills, Knowledge, Abilities, and Other Characteristics.
2. Read project materials and extract project facts: name, time, role, users, original workflow, AI-transformed workflow, user-entry-to-result task flow, pain points, architecture, AI Agent/RAG/LLM design, AI engineering practices, performance/cost optimization, usage/value evidence, delivery evidence, and responsibility boundary.
3. Map project facts to JD requirements. Mark each important ability as strong match, weak match, gap, or not writable.
4. Ask concise questions if project materials, JD, role boundary, or evidence for strong claims is missing.
5. Draft using `assets/project-experience-case-template.md`.
6. Validate with `python .codex/skills/write-ai-architect-project-experience/scripts/validate_project_experience.py --mode case <output-file>`.
7. Review with `references/quality-gates.md`; revise until the result is ready for HR and interviewers.

### 2. Review And Rewrite Case

Use when the user provides an existing project-experience document and asks for review, scoring, diagnosis, optimization, or rewriting.

Steps:

1. Read the existing project-experience document and any provided JD or project materials.
2. Score the existing document out of 100 using `references/quality-gates.md`.
3. List concrete issues by severity: structure, JD match, project clarity, business-process transformation, Agent architecture depth, AI engineering depth, responsibility boundary, delivery evidence, writing style, and risky claims.
4. Give targeted modification advice, not generic writing tips.
5. Rewrite the document using `assets/project-experience-case-template.md`.
6. Validate the rewritten document with `validate_project_experience.py --mode case`.
7. Provide the score, issue summary, and rewritten final version. If writing into a file, preserve the review notes separately from the final project-experience body unless the user asks otherwise.

## Input Gate

Pause and ask concise questions when:

- Generate Case lacks either a JD or project description.
- Review And Rewrite lacks the existing project-experience document.
- Project name, time, role, personal responsibility boundary, or core technical facts are unclear.
- The user wants claims such as `主导`, `上线`, `规模化推广`, hard metrics, customer recognition, or confidential details without evidence.

When evidence is weak, use conservative language such as `完成 PoC/MVP 验证`, `打通关键链路`, `形成方案`, `沉淀工程实践`, or `支撑后续迭代`.

## Output Rules

- Write in Chinese by default.
- Keep technical terms such as RAG, LLM, Agent, Tool Calling, Workflow, Prompt, Schema, Trace, Guardrails, and MCP only when they add precision.
- Start from business context and role value, then explain architecture and AI engineering.
- Make personal contribution boundaries explicit; do not turn team outcomes into individual claims.
- Do not invent metrics, production status, customer recognition, budgets, awards, team size, or rollout scope.
- Prefer natural expert prose over mechanical formulas, slogans, and empty verb piles.
- A strong final case should implicitly answer: original workflow, AI-transformed workflow, user entry to delivered result, why this architecture was chosen, how the Agent was constrained/validated/optimized, and what the writer personally delivered.
