---
name: phase4-game-orchestrator
description: "Use when the user invokes \"게임 만들자\", \"미니게임\", \"바이브코딩\", \"Godot\", \"Phaser\", \"Three.js\", \"ComfyUI 이미지\", \"Suno BGM\", or \"/phase4-game\". Phase 4 (Q3 2026 게임 트랙) orchestrator placeholder. Produces (1) Godot 게임 scaffold + asset list, (2) 42morrow 바이브코딩 시리즈 reference 추천, (3) ComfyUI 이미지 + Suno BGM 자동 생성 파이프라인 sketch, (4) Play Store ASO sketch (안드 출시 후 release notes 톤 유지). Do NOT use before Phase 4 (7월). 현재 placeholder, Phase 4 진입 시 본격 작성."
allowed-tools: Read, Bash, Write
version: 0.1.0
author: simon-stack
---

# phase4-game-orchestrator (Phase 4 placeholder)

> **상태**: ⏳ Phase 4 (Q3 2026, 7월~9월) 진입 시 본격 작성. *현재 placeholder*.

## 발동 조건

- `게임 만들자`, `미니게임`, `바이브코딩`
- `Godot`, `Phaser`, `Three.js`, `Unity`
- `ComfyUI 이미지`, `Suno BGM`
- `/phase4-game`

## Phase 4 진입 전 점검

| # | 조건 | 현재 상태 |
|---|---|---|
| 1 | Godot 4.6.3+ 설치 | ✅ (winget) |
| 2 | ComfyUI 활성 (데스크톱 GPU) | ⏳ install 확인 / 활용 X |
| 3 | Suno Pro 구독 ($10/월) | 🚫 Phase 4 시점 결정 |
| 4 | 5/30 안드 앱 출시 후 Play Console 학습 데이터 | 🚫 5/30 이후 |
| 5 | 42morrow 바이브코딩 시리즈 13+ 글 reference | ✅ raw/clipped/blog-42morrow/DIY-테스트/ |

## 본격 활성 시 산출물 (예정)

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
│   ├── images/  (ComfyUI 생성)
│   └── audio/   (Suno 생성)
└── export_presets.cfg
```

### 2. 42morrow 바이브코딩 시리즈 reference 추천

본인 raw/clipped/blog-42morrow/DIY-테스트/ 의 *13+ 바이브코딩 시리즈*:
- 온라인 빙고 게임
- 루빅스 큐브
- 스틱맨 댄스
- 디지털 렌티큘러 사이니지
- 모스부호 송수신기
- 별자리 보기
- 보석 십자수
- ... 등

→ 사용자 의도 매칭 후 *해당 글 본문 + 기술 스택 + 게임 logic 추출*.

### 3. ComfyUI 이미지 + Suno BGM 파이프라인

```
[게임 컨셉] → ComfyUI workflow → asset images (PNG/sprite)
            → Suno API → BGM (loop / SFX)
            → Godot import 자동 (asset 폴더 watcher)
```

### 4. Play Store ASO sketch

5/30 안드 앱 출시 후 *release notes 톤 유지* + 게임 ASO:
- title + keywords + screenshots 최적화
- *human-voice-guard* 스킬 연동 (AI tell 제거)
- *viral-launch* 4채널 (인앱 / 인스타 / 커뮤니티 / 입소문)

## 현재 placeholder 동작

```
사용자: /phase4-game "스틱맨 게임 만들고 싶어"
→ 본 skill 응답:

  ## Phase 4 진입 전 상태
  Phase 4는 7월~9월 (Q3) 본격 활성. 현재 (5월) 진입 전.

  대신 진행 가능:
  - 42morrow 바이브코딩 스틱맨 댄스 글 fetch:
    raw/clipped/blog-42morrow/DIY-테스트/[바이브코딩] 스틱맨 댄스 만들기.md
  - Godot install 확인: godot --version
  - ComfyUI 활성: 데스크톱 GPU 호스트

  본격 작업은 Phase 4 진입 (7월) 후 진행 권장.
```

## 교차참조

- `wiki/entities/tools/blog-42morrow` § 바이브코딩 시리즈
- `wiki/entities/tools/toolstack-now` § Phase 4-5 도구 (Godot · Blender · Krita · Inkscape · Ollama · ComfyUI)
- `viral-launch` skill (Phase 4 출시 4채널)
- `human-voice-guard` skill (AI tell 제거)

---

*v0.1.0 placeholder 2026-05-25. v1.0 정식 활성: Phase 4 진입 (7월 1주차) 시.*
