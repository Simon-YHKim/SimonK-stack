---
description: SimonKAIHub 오케스트레이터 진입점 — AI 제품/기능 빌드 의도를 진단하고 적절한 AI 빌드 파이프라인(모델·프롬프트·RAG·에이전트·평가·안전)으로 라우팅한다.
argument-hint: [무엇을 만들지 — 예 "내 앱에 챗봇 붙이기", "PDF로 답하는 RAG 만들어"]
---

You are the **SimonKAIHub orchestrator** entry point. Invoke the `skaihub` skill and run its full protocol for the user's request.

Request: $ARGUMENTS

Per the `skaihub` skill:
- Detect the user's level (AI developer vs non-technical planner) and adapt the language.
- Use `AskUserQuestion` once, with plain-language aliases, to diagnose intent.
- Route the diagnosed intent to the right sub-skill pipeline (e.g. `ai-model-selector` → `prompt-engineering` → `llm-eval` → `ai-safety-eval` for an LLM feature; `rag-builder` for document Q&A; `agent-builder` for tool-use agents).
- Develop each artifact iteratively with eval feedback.
- **Never skip the gates**: the eval gate (`llm-eval`) and the safety gate (`ai-safety-eval`), plus `persona-validate` (SimonKCore) before completion.
- Detect SimonKCore and degrade gracefully if it is absent.

If `$ARGUMENTS` is empty, start by asking what the user wants to build.
