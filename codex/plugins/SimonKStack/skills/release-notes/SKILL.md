---
name: release-notes
description: "Use when the user ships an update and needs to write release notes, patch notes, or announcement copy—triggers \"릴리즈 노트\", \"패치 노트\", \"업데이트 공지\", \"플레이스토어 업데이트 내용\", \"앱스토어 업데이트 노트\", \"changelog 정리\", \"공지 작성\", \"release notes\", \"patch notes\", \"app store update copy\", \"what's new copy\". Produces TWO separated artifacts in one pass: (1) developer-facing notes (CHANGELOG.md entry, GitHub release body, PR body — detailed, technical, links commits/issues) and (2) user-facing copy (Play Store/App Store/in-app banner — short, benefit-led, no jargon, max 500 chars, plain human voice). Pulls the actual diff and commit log to avoid hallucination, separates internal-only changes from user-visible ones, and runs each output through the human-voice-guard heuristics."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon-stack
---

# release-notes

업데이트 출시 시 **개발자용 노트**와 **사용자용 공지**를 한 번에, **분리해서** 생성합니다.

## 핵심 원칙

사용자가 반복적으로 강조한 원칙:

> "GitHub README는 상세하게, Google Play 업데이트 내용은 수정사항을 최소한으로 요약하고 효과를 담백하게 전달한다."

→ **하나의 commit 묶음을 두 가지 어조로 변환**하는 것이 이 skill의 본질.

## 트리거

- "릴리즈 노트 만들어줘"
- "패치 노트 작성"
- "스토어 업데이트 내용 써줘"
- "이번 버전 공지문"
- "what's new copy"

## 입력

1. `git log <prev-tag>..HEAD --oneline` 또는 사용자 지정 범위
2. `git diff <prev-tag>..HEAD --stat`
3. (선택) 해당 범위의 PR description, issue 링크

## 워크플로

### 1. 변경사항 분류 (LLM 작업)

각 commit 을 다음 카테고리로 분류:

| 카테고리 | 사용자 노출 | 개발자 노출 |
|---|---|---|
| 새 기능 (feat) | ✅ | ✅ |
| 사용자 영향 버그 수정 | ✅ | ✅ |
| 내부 리팩토링 | ❌ | ✅ |
| 의존성 업데이트 | ❌ | ✅ (보안만 강조) |
| 문서/주석 | ❌ | △ |
| CI / 인프라 | ❌ | △ |
| 성능 개선 (체감) | ✅ | ✅ |
| 성능 개선 (미세) | ❌ | ✅ |

### 2. 개발자용 산출물

**CHANGELOG.md entry** (Keep a Changelog 형식):
```markdown
## [1.4.0] - 2026-05-19

### Added
- 다크모드 전체 화면 지원 (#142)
- 오프라인 캐시 (최근 50개 항목)

### Fixed
- 안드로이드 13 푸시 알림 깨짐 (#156)

### Changed
- 로그인 토큰 갱신 주기 24h → 7d

### Internal
- ESLint 9 마이그레이션
```

**GitHub Release body**: CHANGELOG entry + 다음 항목
- 주요 기여자
- 마이그레이션 노트 (있으면)
- breaking changes (있으면 ⚠️ 강조)

**PR description**: 위 + screenshot 영역

### 3. 사용자용 산출물

**Google Play / App Store "what's new"** (≤ 500자, 한국어 + 영어):

```
🌙 다크모드를 지원합니다
📡 인터넷이 끊겨도 최근 본 항목을 다시 볼 수 있어요
🔔 안드로이드 알림이 더 안정적으로 동작합니다
```

원칙:
- **수정사항 ≠ 효과**. "ESLint 9 마이그레이션" ❌ → 사용자는 신경 안 씀
- **기능명 → 이득**. "다크모드 toggle 추가" ❌ → "다크모드를 지원합니다" ✅
- **이모지 1줄에 1개 이하**. 과하면 노이즈
- **숫자 구체화**. "더 빠르게" ❌ → "최근 50개 항목" ✅
- **AI 어투 금지**. `human-voice-guard` heuristics 적용 (아래 § 어투 가드)

**앱 내 배너 / 푸시 (1줄, ≤ 60자)**:
```
다크모드가 추가됐어요. 설정에서 켜보세요.
```

### 4. 어투 가드 (필수)

생성 후 다음 체크:
- "혁신적인", "강력한", "원활한", "최적화된" → 삭제 또는 구체화
- "~을 도와드립니다", "~을 제공합니다" → 능동형으로
- 영어 직역체 ("그것은 ~합니다") → 자연 한국어
- 이모지 과다 → 메시지당 0-2개

`human-voice-guard` skill 과 연동 — 가능하면 그 skill 의 heuristics 실행.

## 산출 파일

```
release-notes/
├── CHANGELOG-entry.md       ← CHANGELOG.md 에 prepend
├── github-release.md        ← GitHub release body
├── store-listing-ko.txt     ← Play/App Store 한국어
├── store-listing-en.txt     ← 영어
└── in-app-banner.txt        ← 앱 내부 알림 1줄
```

사용자가 직접 복붙해서 각 채널에 게시.

## 안티패턴

- ❌ 모든 commit 을 사용자 공지에 나열
- ❌ "다양한 버그를 수정했습니다" (구체성 0)
- ❌ "여러분의 소중한 의견을 반영하여..." (관용어 인플레이션)
- ❌ 이모지 도배 (🎉✨🚀)
- ❌ 영어 마케팅 직역 ("게임 체인저")

## Related Skills

- `human-voice-guard` — 어투 검사 (이 skill 의 § 4 단계)
- `document-release` — README/ARCHITECTURE 본문 동기화 (다른 도메인)
- `ship` — 릴리즈 전체 워크플로의 일부
- `commit` — Conventional Commits 작성

## 의존

- `git log`, `git diff` 사용 가능해야 함
- 이전 tag (`git describe --tags --abbrev=0`) 또는 사용자 지정 범위 필요

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
