---
name: phase4-game-orchestrator
description: "Use when asked to \"게임 만들자\", \"미니게임\", \"바이브코딩\", \"Godot\", \"Phaser\", \"Three.js\", \"ComfyUI 이미지\", \"Suno BGM\", or /phase4-game-orchestrator. Produces a game feasibility check, playable-prototype scope and asset plan, then continues requested implementation through /vibe. Never assumes an old phase date, installed tools, free music credits or store publishing authority."
allowed-tools: Read, Bash, Write
version: 0.1.1
author: simon-stack
---

# phase4-game-orchestrator (game-track draft)

> **상태**: 게임 트랙 절차 초안. 과거 일정만으로 작업을 막지 않는다. 실제 게임·에셋 생성 및 스토어 제출은 도구·권한·비용·결과를 각각 확인한다. 이 문서만으로 제작 자동화가 구현된 것은 아니다.

## 발동 조건

- `게임 만들자`, `미니게임`, `바이브코딩`
- `Godot`, `Phaser`, `Three.js`, `Unity`
- `ComfyUI 이미지`, `Suno BGM`
- `/phase4-game-orchestrator`

## 착수 전 실측

| # | 확인할 것 | 판정 기준 |
|---|---|---|
| 1 | 선택 엔진 | 현재 프로젝트 선호와 실제 CLI·에디터 설치·버전을 확인한다. |
| 2 | ComfyUI·GPU | 로컬 워크플로와 자산 사용 권한을 확인한다. 미확인이면 생성 가능하다고 말하지 않는다. |
| 3 | Suno 등 음악 서비스 | 구독 포함 사용·추가 과금 차단·라이선스를 확인하기 전 호출·구독·결제를 하지 않는다. 불명확하면 사용 가능한 로컬 임시 오디오를 확인하거나 무음 에셋으로 진행한다. |
| 4 | Play Console·출시 데이터 | 실제 계정·앱 상태를 관측하기 전 출시·게시 가능 상태라고 가정하지 않는다. |
| 5 | 42morrow 참고 자료 | 허용된 로컬 경로에 파일이 실제 존재할 때만 읽고 추천한다. 문서 수를 가정하지 않는다. |

## 요청에 따른 산출물 (도구 검증 후)

### 1. Godot 게임 scaffold

```
project_name/
├── project.godot
├── scenes/
│   ├── main.tscn
│   └── ui/
├── scripts/
│   ├── player.gd
│   └── enemy.gd
├── assets/
│   ├── images/  (확인된 로컬 워크플로 또는 임시 에셋)
│   └── audio/   (사용권이 확인된 오디오 또는 임시 에셋)
└── export_presets.cfg
```

### 2. 42morrow 바이브코딩 시리즈 reference 추천

접근 가능한 `raw/clipped/blog-42morrow/DIY-테스트/` 자료가 있을 때 참고할 수 있는 주제 예시:
- 온라인 빙고 게임
- 루빅스 큐브
- 스틱맨 댄스
- 디지털 렌티큘러 사이니지
- 모스부호 송수신기
- 별자리 보기
- 보석 십자수
- ... 등

→ 실제 파일 존재·열람 권한을 확인한 뒤 사용자 의도에 맞는 글의 기술 스택과 게임 로직을 참고한다.

### 3. 이미지·음악 파이프라인 초안

```
[게임 컨셉] → 확인된 로컬 이미지 워크플로 또는 임시 에셋
            → 사용권·비용이 확인된 오디오 또는 로컬 임시 오디오
            → 선택 엔진의 에셋 import 및 라이선스 기록
```

### 4. Play Store ASO 초안 (게시 전 별도 확인)

실제 앱·계정·게시 권한을 확인한 뒤 *release notes 톤 유지* + 게임 ASO 초안:
- title + keywords + screenshots 최적화
- *human-voice-guard* 스킬 연동 (AI tell 제거)
- *viral-launch* 4채널 (인앱 / 인스타 / 커뮤니티 / 입소문)

## 현재 초안의 동작 경계

```
사용자: /phase4-game-orchestrator "스틱맨 게임 만들고 싶어"
→ 본 skill 응답:

  - 현재 프로젝트·선호 엔진과 로컬 설치를 확인한다.
  - 접근 가능한 42morrow 자료가 있으면 실제 내용을 읽어 참고한다.
  - 추가 과금 없이 가능한 플레이어 이동·충돌·재시작의 최소 플레이 루프와 에셋 목록을 정한다.
  - 사용자가 구현을 요청했다면 초안만 제출하고 완료라고 하지 않는다. /vibe의 빌드·검증 절차로 이어간다.
  - ComfyUI·Suno 생성 또는 Play Store 게시를 준비·실행했다고 주장하지 않는다.
```

## 교차참조

- `wiki/entities/tools/blog-42morrow` § 바이브코딩 시리즈
- `wiki/entities/tools/toolstack-now` § Phase 4-5 도구 (Godot · Blender · Krita · Inkscape · Ollama · ComfyUI)
- `viral-launch` skill (Phase 4 출시 4채널)
- `human-voice-guard` skill (AI tell 제거)

---

*v0.1.1: 오래된 일정·설치·가격 단정을 제거했다. 실제 게임 제작 자동화는 별도 구현·검증이 필요하다.*

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
