---
project: 2nd-B
repo: https://github.com/Simon-YHKim/2nd-B
clone: E:\2ndB
app-name: 2nd-brain (v0.0.1)
stack: Expo ~56 / React Native 0.85 (managed) · NativeWind(Tailwind) · Supabase(백엔드·계정·데이터) · Vercel(web 배포)
default-branch: main
workflow: branch-per-task + PR (asset/* = 디자인·에셋, claude/* = 코딩, qa/* = 검수)
owner: claude
updated: 2026-06-05 15:45:37 KST
phase: build
---

# 2nd-B — HANDOFF (always-latest)

> 메인 앱 프로젝트. 실제 코드/에셋은 **github.com/Simon-YHKim/2nd-B** 에 있고(브랜치-per-작업 + PR), 이 허브는 **코디네이션 채널**이다. 메시지는 브랜치·PR·커밋·스크린샷을 **링크로** 참조한다(코드 자체를 허브에 복사하지 않음).

## 개요
- "2nd-brain" — Expo(RN) 크로스플랫폼 앱. 로컬 클론 `E:\2ndB`(main, 클린). node_modules 설치됨.
- 작업 시 **프로젝트 자체 컨텍스트 필독**: `E:\2ndB\CLAUDE.md` · `CONTEXT.md` · `DESIGN.md`.
- 품질 게이트: `npm run verify` (lint+type-check+i18n+lexicon+llm-boundary+constraints+no-emdash+jest). **머지 전 반드시 통과.**

## 역할 ↔ 브랜치 매핑
- **Claude(코딩)** → `claude/*` 브랜치, PR로 main 병합.
- **Codex(이미지·UI/UX)** → `asset/*` 브랜치(디자인·에셋), UI 스펙은 허브 메시지로 전달.
- **Antigravity(네이티브 검수)** → 빌드/브랜치 QA, 리포트는 허브 메시지로. 코드 수정 필요 시 Claude로 request.

## 현재 상태
- 설계(codex):
- 구현(claude):
- QA(antigravity):

## 라이브 검증 사이클
- 대단위 사이클 종료 + 사용자 라이브 확인 필요 시: push → PR로 main 머지 → 라이브 화면 제공 (PROTOCOL §8).
- **라이브 화면 수단 (확정 — Expo managed 기준)**:
  - **빠른 UI 확인** = `npm run web` (`expo start --web`) → 로컬 웹 → 스크린샷. 에뮬 불필요, 가장 빠름.
  - **네이티브 확인** = `npx expo run:android` → prebuild + 에뮬레이터(AVD `Pixel_9_Pro_XL`) 설치·실행 → 스크린샷. 첫 빌드 느림. **네이티브 검수는 Antigravity 위임.**
  - **계정·데이터 작업(옵션1)** = `vercel.json` + Supabase 이미 구성됨 → Vercel 웹 배포 URL로 제공. (배포 파이프라인 대부분 기존재 → 연결만.)
- 빌드 환경 준비됨: node v24 + npm 11 + node_modules(635) + Android SDK/Studio/JDK17 + AVD `Pixel_9_Pro_XL`.

## 다음 액션
- [ ] 라이브 경로 리허설 1회 (`npm run web` 화면 캡처 — 가장 빠른 검증)
- [ ] 첫 대단위 작업 사이클 받기
- [ ] (계정-데이터 작업 시) Vercel+Supabase 배포 URL 경로 연결 확인

## 산출물 링크
- 코드: (PR/브랜치 링크)
- 디자인/에셋: (asset/* 브랜치)
- QA 리포트: (antigravity outbox)
