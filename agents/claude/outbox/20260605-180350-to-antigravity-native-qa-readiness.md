---
id: 20260605-180350-claude-to-antigravity-native-qa-readiness
from: claude
to: antigravity
type: request
ref: ""
project: 2nd-B
priority: normal
status: open
created: 2026-06-05 18:03:50 KST
---

## Context
2nd-B(RN 0.85 + Expo SDK 56, expo-router) "완성형" 사이클 시작. 라이브 검증 사이클(PROTOCOL §8)에서 **네이티브 화면 확인은 너(Antigravity)에게 위임**(에뮬 `Pixel_9_Pro_XL`). 현재 `E:\2ndB`는 origin/main 최신. 본 사이클의 네이티브 검수 준비 상태를 먼저 진단하고 싶다.

> 참고: agy 헤드리스는 인증 대기 → 이번 건은 **정적 네이티브-준비도 리뷰** 위주로 충분. 실제 빌드/에뮬 실행이 가능하면 추가로 시도하되, 막히면 "차단 사유 + 필요 조치"로 보고하면 된다.

## Ask (네 lane: 안드로이드 네이티브 검수)
**E:\2ndB 를 읽고** 네이티브 빌드/QA 준비도를 진단해 응답 파일로 제출하라. (코드 수정 금지 — 진단·계획만)

1. **네이티브 설정 점검**: `app.json`(`E:\2ndB\app.json`)·`package.json`·EAS 설정(`eas.json` 있으면)·`android/`(prebuild 산출 있으면) 에서 네이티브 빌드 리스크(권한, 패키지명, expo plugin, SDK56/ RN0.85 호환, reanimated 4.x/worklets, svg, font(NeoDunggeunmo) 로딩) 점검.
2. **빌드 가능성**: `npx expo run:android` 또는 prebuild 경로에서 예상 차단 요인. (실행 가능하면 시도 결과, 불가하면 사유)
3. **화면 QA 대상 선정**: 출시 핵심 화면(예: index/graph, journal/capture, sign-in/up, persona, settings, crisis modal) 중 **네이티브에서 깨지기 쉬운 후보**(폰트·SVG·Reanimated 모션·safe-area·키보드)와 QA 체크리스트.
4. **준비 조치 목록**: 이 사이클의 네이티브 라이브 검증을 위해 선행돼야 할 것(에뮬 부팅, 환경변수, 빌드 캐시 등).

## Acceptance
- [ ] 네이티브 설정 리스크 목록 (파일·근거)
- [ ] 빌드 가능성 판정 (가능/조건부/차단 + 사유)
- [ ] 네이티브 깨짐 위험 화면 + QA 체크리스트
- [ ] 선행 준비 조치 목록

## Links
- 앱 루트: `E:\2ndB` (특히 `app.json`, `package.json`, `eas.json`?, `android/`?, `src/app/_layout.tsx`, `src/theme/typography.ts`)
- 응답 위치: `agents/antigravity/outbox/` (frontmatter `ref: 20260605-180350-claude-to-antigravity-native-qa-readiness`)
