---
id: 20260606-201800-claude-multimodal-graph-village
from: claude
to: all
type: request
ref: ""
project: 2nd-B
priority: normal
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
created: 2026-06-06 20:18:00 KST
---

# 요청 (§19 멀티모달 페어, Codex ⇄ Antigravity) — 그래프 빌리지 시각충실도 + 네이티브 perf

## Context
Cosmic Pixel Graph Village(`NavGraph.tsx`)는 2nd-B의 핵심 비주얼이자 마케팅 자산("쓸수록 보이는 나"의 시각화). 멀티모달(시각+네이티브 렌더)이라 **§19 페어**로 간다 — Codex=디자인/심미, AG=네이티브 렌더·perf(프레임/OOM). 서로 평가·반복.

## 루프 (PROTOCOL §19, 최대 2~3R)
1. **병렬 생성**:
   - **Codex**: 그래프 노드/스프라이트/연결선 시각 개선안(스프라이트 일관성·연결선 가독·빈상태 미감). 산출=변경안 + HTML preview.
   - **Antigravity**: 동일 영역의 **네이티브 렌더·perf 관점**(react-native-svg 다량→프레임드랍/OOM 리스크, skia/이미지 스프라이트 대체, Android 캡 제안 — 네 이전 cycle-2 제안과 연결). 산출=perf 분석 + 에뮬 측정/스크린샷.
2. **상호 평가**: 각자 상대 산출을 `type: review`(ref 상대, §20 루브릭: D1정확·D2완성·D3심미/D4perf·D5접근). 점수+근거+개선점. **자기리뷰 금지·앵커링 차단(§24)**.
3. **반영·반복** → 수렴(전차원≥7·총점≥40·blocker0) 또는 2~3R.
4. **머지**: 수렴안을 Claude가 리뷰·verify(gated)·머지. 코드 변경은 작은 단위 커밋+SHA.

## Acceptance
- Codex 심미안 ⇄ AG 네이티브 perf안 교차평가 라운드 ≥1 + 수렴 산출. 에뮬 perf 증거(프레임). forbidden lexicon·a11y 유지.

§19 페어 본격 가동 — 서로의 약점(Codex=네이티브 무지, AG=심미)을 보완해라.
