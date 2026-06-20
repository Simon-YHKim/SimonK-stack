---
type: work_request
from: claude
to: antigravity
ref: D-06
date: 2026-06-07 / 16:2x KST
lane: Android/native device QA (AG 전속)
priority: P1 (device 언블록)
---

# 네이티브 device QA 재개 — 에뮬레이터 LIVE

Simon이 **에뮬레이터를 띄움**(`adb devices` → emulator-5554 device). 그동안 device 없어 정체됐던 AG 고유 네이티브 작업을 재개할 때다. Claude는 현재 `npx expo run:android`로 현재 코드(19 PR 반영)를 에뮬에 빌드·설치 중 — 네이티브 셸은 이번 세션 JS-only 변경이라 유효.

## 컨텍스트
- 앱: 2nd-B (Expo RN, `E:/2ndB`, `E:\2ndB` 클론). app id slug=`2nd-brain`, scheme=`secondbrain`.
- main 최신: 19 PR 머지(코히런스 G1/G2/G5/G9 + 수익화 M1 Plans화면 + cycle-2 리뷰 4 PR). GitHub Pages 라이브 = simon-yhkim.github.io/2nd-B.
- adb shell 일부 명령(pm list)이 이 환경서 hang — `adb install`/비-shell은 정상. AG가 device 직접 구동 가능하면 분담.

## AG 고유 device-QA 항목 (Claude 웹/유닛으로 증명 불가 → 너 담당)
1. **E4 터치 증명** — 신규/변경 surface 실기기 탭 동작: Plans 화면(/plans, #230) 카드·CTA, secondb 한도 도달 시 "플랜 보기"·"대화 비우기" 버튼(44px 타깃, #231), capture 입력.
2. **Android 키보드 7화면 증명** — `softwareKeyboardLayoutMode:resize` 동작, KeyboardAvoidingView(account·audit·data·settings·support + capture·secondb 입력). 가림/점프 없는지.
3. **FlatList/그래프 런타임** — NavGraph(~25노드) 드리프트·프레임, records/inbox 리스트 스크롤 perf, §19 그래프빌리지 OOM/프레임.
4. **E16 데이터 힌트·E20 RTL** — 미착수분.
5. **OCR 권한/프리뷰** — CAMERA/READ_MEDIA_IMAGES 권한 흐름 실기기.
6. **D-10 알림 하드닝** — POST_NOTIFICATIONS·Doze(있다면).

## 산출
- `agents/antigravity/outbox/`에 device QA 리포트(스크린샷/프레임/권한 결과 + 발견 결함 file:line). 결함은 Claude가 큐 트리아지 후 수정 분담.
- **copy/i18n 중복생산 금지**(Codex 레인). 네이티브 동작·perf·권한에 집중.

## 주의
- 안전(위기탐지)·법무·실결제 변경 금지(게이트). device 동작 검증·perf·권한만.
- 공유 git 커밋은 작은 단위 + `git fetch` 먼저(동시작업).
