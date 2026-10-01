# SimonK-Stack

> **스킬을 한 요청으로 조합하는 라이브러리.** `/vibe`가 메인 조정자이고, `simonk`는 그 아래의 스프린트 절차입니다. 사용자 = 목표와 권한의 결정자.

![version](https://img.shields.io/badge/version-0.1.0-5b8cff) ![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml) [![source skills](https://img.shields.io/badge/source%20skills-141-brightgreen)]() [![harness](https://img.shields.io/badge/simonK-autonomous-blueviolet)]()

**Site**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) · **English**: [README.en.md](README.en.md) · **자매 레포**: [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (PRIVATE) — 세션 간 학습 누적

---

## 설치 / Install

> **소스 전용 머지 안전 경계(D-33):** 이 브랜치의 `/vibe` 2.12.35는 조건부 호스트 이미지 어댑터와 Codex CLI 읽기 전용 어댑터를 포함하지만, 둘 다 소스·검증 경로이며 사용자 설치본이 아닙니다. Grok CLI 모델 목록도 메타데이터로만 읽으며 계정·쿼터·effort·구독 포함이 확인된 실행 경로는 아닙니다. 최신 격리 후보는 2.12.35이며 사용자 flat 설치본은 2.12.24입니다. 이미지 어댑터에는 실제 호스트 구현이 없고, 현재 노출된 이미지 도구는 구독 전용 USD 0 하드캡·요청 조회를 증명하지 못해 이미지 생성은 계속 차단됩니다. Codex CLI 어댑터도 정확한 계정·모델·effort·구독 포함·크레딧 폴백 차단 증거 없이는 실행하지 않습니다. `distribution/main-source-only.hold`가 있는 체크아웃의 SessionStart 훅은 사용자 홈·업데이트 확인을 건드리지 않고 종료하며, `main` push의 자동 GitHub 릴리스도 보류합니다. 루트 Claude marketplace의 기존 `simonk-stack` 플러그인도 머지 전 `main` 커밋 `313c04b`에 고정했습니다. 이 장치들은 다섯 플러그인 후보를 설치하거나 자동 라우팅의 실사용 품질을 증명하지 않습니다. 새 릴리스 전에는 보류 파일 제거와 marketplace 핀·버전 변경을 별도 검증하세요.

> **최신 격리 후보:** `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-billing-consistency-candidate/`는 `/vibe` 2.12.35 소스입니다. Codex 사용량의 비표준 버킷과 모순 금액, Grok 초과 사용 플래그의 상충 표기를 차단합니다. Claude 5플러그인·182스킬, Codex 안전 부분집합 177스킬, 네 영수증·오프라인 probe 4/4, 단위 테스트 333건·자체 점검 180항목·스킬 품질 141/141을 확인했습니다. 정확한 새 바이트의 네트워크·인증정보 차단 Sandbox에서 Claude Code 2.1.285와 Codex CLI 0.155.0의 적재·두 차례 복원도 통과했습니다. 실제 사용자 설치, 모델·이미지·Bot 호출, 자동 선택 품질 및 구독 청구는 미검증입니다. `installation_ready=false`, `host_compatibility_verified=false`, `runtime_closure_verified=false`를 유지합니다. 자세한 영수증과 원시 결과는 [설치·후보 검증 절차](docs/INSTALL.md)를 보세요. 2.12.33·2.12.34 격리 후보는 최종 소스와 다르므로 배포 대상으로 사용하지 않습니다.

> **2026-10-01 소스 머지 후 상태:** D-38에 따라 #68·#69는 소스 전용으로 `main`에 머지됐고 Pages 자동 배포만 허용됐습니다. D-39에 따라 사용자 설치는 계속 보류 중입니다. 새 읽기 전용 `scripts/vibe_host_preflight.py`에서 현재 Core 링크 8/8을 관측했고 Claude·Codex의 `/vibe` 본문 2개만 후보와 달랐습니다. 이는 전체 182/177스킬 설치·명령 선택·청구 검증이 아니며 `installation_ready=false`입니다. [실행 방법과 한계](docs/INSTALL.md#사용자-flat-링크-읽기-전용-사전검사)를 확인하세요.

> **전체 flat 스킬 감사:** 같은 검사기의 후보 대비 SKILL.md 범위는 Claude 182개 중 일치 4·변경 134·미설치 44, Codex 안전 부분집합 177개 중 일치 4·변경 128·미설치 45입니다. 8개 Core 링크의 구조가 정상이어도 전체 설치·명령 선택·스크립트 자산·실호출 준비를 의미하지 않습니다.

> **네이티브 플러그인 목록:** 현재 Claude·Codex의 후보 5개 등록 일치는 각각 0/5입니다. 사전검사기에 두 CLI의 `plugin list --json` 관측값을 전달해 버전·활성 상태까지 비교할 수 있지만, 목록 일치만으로 플러그인 바이트나 명령 선택을 검증할 수는 없습니다.

> **고정 후보 바이트 검사:** 읽기 전용 사전검사에 소스·Claude·Codex overlay·Codex 안전 부분집합의 네 SHA-256 digest를 명시하면 네 패키지 파일과 출처 체인을 검사합니다. 현재 2.12.35 후보는 4/4 일치하지만 이는 사용자 설치·호스트 명령 선택·구독 청구 검증이 아닙니다. [실행 명령과 게이트](docs/INSTALL.md#사용자-flat-링크-읽기-전용-사전검사)를 보세요.

> **이전 격리 후보:** `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-top-credit-candidate/`는 명명된 한도 버킷에 0 크레딧이 있더라도 최상위 크레딧 기록이 없으면 차단하는 `/vibe` 2.12.32 소스입니다. Claude 5플러그인·182스킬, Codex 안전 부분집합 177스킬, 네 영수증·오프라인 probe 4/4, `/vibe` 단위 테스트 327건·자체 점검 180항목·스킬 품질 141/141이 통과했습니다. 정확한 해당 후보의 네트워크·인증정보 차단 Sandbox에서 Claude Code 2.1.285는 플러그인 5개·182스킬, 고정 Codex CLI 0.155.0은 플러그인 5개 활성화와 기존 링크 두 차례 복원을 통과했고 두 게스트는 종료했습니다. 이 후보는 비표준 버킷 이름·형식의 구매 크레딧을 수집 단계에서 버릴 수 있어 배포 대상으로 사용하지 않습니다.

2026-10-01 추가 격리 시험에서는 사용자가 의도적으로 고정한 Codex CLI **0.155.0**으로 이전 2.12.29 후보의 플러그인 5개를 활성화하고 기존 Claude·Codex 링크를 두 차례 복원했습니다. 게스트의 인증 환경변수·활성 네트워크·모델 생성은 0이었고 게스트를 종료했습니다. 이는 고정 버전의 무인증 적재·복원 증거이지 새 2.12.30 후보나 실제 사용자 프로필 설치, 자동 라우팅 품질 또는 구독 청구 증거는 아닙니다.

> 이전 호스트 진입 재현 후보 `E:/Coding Infra/Releases/SimonK-stack/20260930-main-entry-d77def6/`는 `/vibe` 2.12.17입니다. 같은 읽기 전용 Claude Sonnet 5.5 요청 한 건에서 이전 후보의 `simonk-stack:skstack` 대신 의도한 `simonk-core:vibe`가 실제 `Skill` 도구로 호출됐습니다. 반면 Codex 전체 subset 임시 노출은 스킬 설명 예산을 초과했고, 3스킬 시험에서는 `/vibe`를 골랐지만 본문 읽기가 정책에 막혔습니다. 따라서 **한 사례의 Claude 진입 개선**만 확인됐고 당시 2.12.29 후보의 호스트 선택·Codex 본문 실행·실효 effort·구독 청구는 증명되지 않았습니다. 사용자 프로필은 변경하지 않았으며 아래 레거시 `scripts/install.sh`는 원격 조회와 홈 변경 경로가 있어 이 후보 시험용으로 실행하지 마세요.

2026-10-01 현재 이 PC의 Claude·Codex·`.agents` flat `/vibe` SKILL.md는 모두 2.12.24로 관측됐습니다. 이는 이 브랜치의 2.12.35 소스나 다섯 플러그인의 운영 설치·호스트 자동 선택 검증이 아닙니다. v30의 과거 오프라인 재현에서 당시 2.11.6은 구독 검증·초과 사용 OFF만 참이고 **선택 모델의 구독 포함·API 폴백 차단이 미확인**인 입력을 `ready`로, 2.12.4는 `blocked`로 판정했습니다. 최신 소스는 Codex·Grok CLI·Grok Bot의 기존 구매 크레딧 폴백 차단 증거도 요구합니다. 이 과거 재현은 현재 호스트 과금·자동 선택 품질을 증명하거나 실제 과금 발생을 뜻하지 않습니다. flat 스킬 파일의 존재만으로 추가 과금 $0이나 전체 플러그인 가동을 보증하지 마세요.

2026-09-29 운영 프로필 조회에서는 Claude·Codex의 SimonK 플러그인 등록이 각각 0개이고, 세 flat 스킬 경로에 v30 고유 182스킬 중 138개 이름만 존재합니다. 나머지 44개가 다른 호스트 자원에 없다는 뜻은 아니지만, **현재 프로필에서 다섯 플러그인 전체가 설치·호출 가능하다는 증거는 아닙니다.** 별도 무인증 프로필의 v31b 설치 캐시는 Claude 741/741파일·Codex 724/724파일 해시가 일치했고, 격리 Claude 초기화에서 플러그인 스킬 182개가 로드됐습니다. 이 결과는 실제 사용자 프로필 설치나 자동 스킬 선택의 증거가 아닙니다. 범위는 [v31b 격리 캐시 기록](docs/INSTALL.md#v31b-claudecodex-격리-캐시-2026-09-29)에 있습니다.

Claude Code 마켓플레이스에서 **고정된 기존 루트 플러그인** 설치 (새 다섯 플러그인 후보 설치 명령이 아님):

```
/plugin marketplace add Simon-YHKim/SimonK-stack
/plugin install simonk-stack@simonk-stack
```

> git clone 기반 3-모드 설치(Direct / Vendor / Bootstrap)는 아래 [빠른 시작](#-빠른-시작--3-가지-설치-모드) 참고.

### Codex 스킬 설명 예산

`Skill descriptions were shortened ...`는 초기 선택 목록의 설명이 줄었다는 경고이며, 선택한 `SKILL.md` 본문을 삭제하지 않습니다. 설명은 고유 목적·호출 조건·산출물 위주로 짧게 유지합니다. `/vibe` 진입을 확실히 지정하려면 Codex의 스킬 목록에서 실제 등록 이름을 선택하세요. 플러그인이 namespace를 붙였다면 `$simonk-core:vibe`, 독립 스킬로 등록됐다면 `$vibe`처럼 이름이 다를 수 있습니다.

동일 패키지가 `.agents/skills`와 `.codex/skills`에 따로 복사돼 있으면, 파일·참조를 비교한 뒤 한 경로만 `~/.codex/config.toml`에서 비활성화할 수 있습니다. 이름이 같다는 이유만으로 다른 구현이나 플러그인을 끄지 마세요.

```toml
[[skills.config]]
path = "/absolute/path/to/redundant/skill/SKILL.md"
enabled = false
```

설정 원본을 백업하고 **새 Codex 세션**에서 확인하세요. 선택 경로의 파일은 그대로 두며, 해당 비활성화 항목을 제거하면 복구됩니다. 다른 플러그인 수에 따라 경고가 남을 수 있습니다. [공식 스킬 로딩·비활성화 안내](https://learn.chatgpt.com/docs/build-skills)

Codex의 [공식 설정 참조](https://learn.chatgpt.com/docs/config-file/config-reference)에 따르면 `skills.max_context_tokens`는 초기 스킬 목록 예산이며 기본값은 모델 컨텍스트의 2%, 명시적 상한은 10,000토큰입니다. 격리 프로필에서만 `-c skills.max_context_tokens=10000`을 시험한 결과, 후보 182개는 전역 스킬을 모두 끈 짧은 홈에서만 초기 목록에 전부 표시됐습니다. 이 설정은 본문 로드·자동 선택 품질·훅 동작을 증명하지 않으며, 전역 고유 스킬을 숨기는 일괄 비활성화는 권장하지 않습니다. 실제 사용자 프로필은 변경하지 않았습니다.

본문 보존과 자동 선택 정확도는 별개입니다. [선택 전후 비교 절차](docs/skill-selection-validation.md)는 대표 요청 30개와 오프라인 채점 도구를 제공하며, 실제 Claude/GPT 관측이 없으면 `pending`으로 남깁니다. 단위 테스트 통과를 모델 정확도 통과로 해석하지 마세요.

`/vibe`의 과거 버전 기록을 스킬 본문에서 제거한 2.11.10 변경은 **선택 후 본문 로드량**을 줄입니다. 초기 목록의 description 축약 경고 자체나 자동 선택 정확도 개선을 입증하지는 않습니다.

2.11.11은 과거 Grok 사용량 HOLD를 영구 금지로 취급하지 않습니다. 새 실호출은 최신 쿼터, 선택 모델의 구독 포함 여부, 초과 과금 차단과 지원되는 안전 실행 경로가 확인된 경우에만 가능합니다. 이 버전은 추가 과금·모델 실호출 권한을 만들지 않습니다.

2.11.12는 Antigravity CLI 1.2.12의 `/usage`가 실제로 0턴·0토큰인 것을 확인해 메타데이터 수집만 다시 허용합니다. 모델 목록·계정 과금 방식·실행 권한은 여전히 별도 증거가 필요하며, 구독 포함 경로가 확인되지 않은 모델 실호출은 시작하지 않습니다.

2.11.13은 `/vibe` 설명에 GUI 자연어 진입점, `CLI/API/MCP` 우선 확인과 실제 `vibe-bot` 어댑터 이름을 명시했습니다. 초기 Play Console 평가의 존재하지 않는 스킬 답변은 `--tools ''`로 `Skill`도 제거한 비대표 조건에서 나왔습니다. `Skill` 허용 조건의 단일 후속 응답은 `/vibe`를 선택했고, v9 후보의 명시적 Skill 로드도 관측됐지만 반복 자동 선택 정확도나 다섯 표면 실행을 증명하지는 않습니다. 자세한 평가 조건과 호스트 훅·배포 테스트 범위는 [설치·후보 검증 절차](docs/INSTALL.md)를 보세요. Claude CLI의 USD 필드는 실제 추가 청구 영수증이 아닙니다.

분리 플러그인 후보의 명시적 로컬 파일 참조는 [설치·후보 검증 절차](docs/INSTALL.md#후보-경로-경고-분류-2026-09-27)의 정적 경로 검사로 재현할 수 있습니다. 경로 검사 통과만으로 설치·런타임 준비를 주장하지 않습니다.

이전 `/vibe` 2.12.10 안전 후보는 `E:/Coding Infra/Releases/SimonK-stack/20260930-subset-discovery-39c3ca3/`입니다. Claude·Codex 양쪽의 중앙 17모델 파일 해시는 같고, 공통 176스킬 본문은 바이트까지 같으며 `zoom-out`은 승인된 호스트별 투영 1건입니다. Codex 안전 정책 제외 5개는 D-29대로 유지하되, `subset.json`이 정확할 때만 기본 카탈로그가 177개를 반환하도록 수정했습니다. Claude 기본 카탈로그 182개, Codex 기본 카탈로그 177개, 후보 오프라인 실행 점검과 단위 테스트가 통과했습니다. **이 후보의 실제 호스트 자동 선택·실행 결과 품질과 사용자 프로필 설치는 검증하지 않았습니다.** 이전 후보의 Sandbox 결과는 이 후보의 호스트 검증으로 이월하지 않습니다. 원시 SHA-256·남은 게이트는 후보 폴더의 `report.html`과 [설치·후보 검증 절차](docs/INSTALL.md)에 있습니다. Gstack 전이 런타임, 플러그인별 버전 계약, 실제 사용자 프로필 이관이 남아 설치 준비 플래그는 계속 `false`입니다. 이전 `281fc11`·[v31b](docs/INSTALL.md#v31b-lf-고정-격리-후보-2026-09-29)·[v23 Sonnet 5.5 시험](docs/INSTALL.md#v23-claude-sonnet-55-공개-사실-갱신-후보-2026-09-29)은 과거 후보에 한정됩니다.

그 이전 후보의 별도 빈 로컬 프로필에서는 Claude Code 2.1.285가 5플러그인·182스킬을 초기화했고, Codex CLI 0.159.0은 5플러그인·177스킬을 등록해 캐시 725/725파일 해시가 후보와 일치했습니다. 사용자 핵심 설정 파일 해시는 변하지 않았습니다. 새 Windows Sandbox 시험은 흰 화면에서 결과 없이 멈춰 OS 네트워크 차단 검증으로 인정하지 않았습니다. 자세한 범위는 [설치·후보 검증 절차](docs/INSTALL.md#39c3ca3-d-29-제외본-발견-수정-후보와-별도-로컬-호스트-적재-2026-09-30)를 보세요. 자동 선택·실행 품질과 구독 과금 안전성은 여전히 미검증입니다.

v23에서는 Claude Code 2.1.284로 호스트 실행 파일이 바뀐 뒤에도 별도 격리 게스트의 초기화·736파일 설치를 재검증했고, Claude/Codex 합성 기존 프로필에서는 다른 테스트 플러그인·개인 스킬이 보존됐습니다. 이는 v28의 모델 선택·호스트 런타임 검증이나 실제 사용자 프로필의 무손실 이관·운영 설치 준비를 뜻하지는 않습니다.

이전 `/vibe` 2.12.1 격리 후보는 `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-model-facts/`입니다. [v20 검증 기록](docs/INSTALL.md#v20-모델-근거-및-격리-설치-리허설-2026-09-28)에는 공식 모델 근거 갱신, Claude·Codex 무인증 Sandbox의 5플러그인 설치·철회와 734/740파일 해시 일치, Claude `--init-only`의 5플러그인·182스킬 로딩, 고정 Gstack 시작 절차 55개 분리 시험이 있습니다. 별도 [Gstack 격리 설치 기록](docs/INSTALL.md#고정-gstack의-격리된-프로젝트-로컬-설치)은 공개 의존성을 받은 새 게스트에서 Gstack 단독 Claude 프로젝트 로컬 엔트리 57/57과 일반 실행 파일 생성을 확인했습니다(Playwright bootstrap·CSO 제외). 모두 빈 게스트의 제한 검증입니다. Gstack helper를 직접 참조하는 31개 스킬의 전이 실행 의존성과 기존 사용자 프로필 호환성은 남아 있고, 정적 감사의 직접 참조 646곳·고유 대상 9개는 런타임 폐쇄를 뜻하지 않습니다. 사용자 설치본은 이 후보로 전환하지 않았으며, 패키지·Sandbox 테스트는 모델·Bot·Orca 실호출이나 구독 과금 안전성의 증거가 아닙니다. 특히 Claude Fable의 비대화형 호출은 사용량 크레딧을 동의창 없이 청구할 수 있으므로, 정확한 모델·계정 경로의 구독 포함과 초과 과금 차단 증거가 없으면 실행하지 않습니다.

추가 [동시 초기화 기록](docs/INSTALL.md#gstack-프로젝트-스킬과-v20-플러그인-동시-초기화)은 새 게스트에서 Gstack 프로젝트 스킬 57개와 v20 플러그인 스킬 182개를 함께 로딩하고 중복 건너뜀 0을 확인했습니다. 이는 임시 `--plugin-dir` 초기화 시험이며 실제 설치·전체 동작 검증은 아닙니다.

---

## 회사 비유 — 한 페이지로 보기

```
                  ┌─────────────────────────┐
                  │  사용자 = Founder / CEO │
                  └────────────┬────────────┘
                               │
                  ┌────────────▼────────────┐
                  │  /vibe = Main coordinator│  ← simonk 등 필요한 절차 선택
                  └────────────┬────────────┘
                               │
   ┌───────────┬───────────┬───┴───────┬───────────┬───────────┬───────────┬───────────┐
   ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
Strategy   Product    Engineering DevEx      Security   Growth     Knowledge  Skill
Office     & Design               & Platform & Compl.   & Revenue  & Memory   DevOps
```

각 부서 = skill 묶음. 같은 책임은 같은 부서, 다른 책임은 다른 부서.

---

## 🏢 8 부서 — 무엇을 어디서 처리하나

### 1. Strategy Office (전략실) — 비전·계획·의사결정

새 프로젝트 시작 시 *무엇을 왜* 만들지 결정. /vibe가 목표에 맞춰 필요한 기획 절차를 선택합니다.

| 핵심 skill | 역할 |
|---|---|
| `/founder-context` | me.md / vision.md / design.md / workingstyle.md 4-file 부트스트랩 — 창업자의 정체성·비전·디자인·작업 패턴을 한 번에 |
| `/office-hours` (gstack) | YC 파트너 스타일 6-Q forcing question — "이거 만들 가치 있나?" |
| `/plan-ceo-review` (gstack) | 10-star 스코프 재정의, 임원실 한 명이 본 후 plan 락 |
| `/plan-eng-review` (gstack) | 엔지니어링 리더 시각으로 plan 검증 |
| `/spec` (gstack) | 모호한 의도를 실행 가능한 spec 으로 5-phase 변환 |
| `/grill-me` | 1Q-at-a-time 인터뷰로 plan/spec stress test (simon-tdd RED 전) |

### 2. Product & Design (제품·디자인) — UI·UX·시각 방향

전략실이 *왜* 정하면 여기가 *어떻게 보일지* 정한다. 코드 작성 전에 톤·레퍼런스·폰트·팔레트 확정.

| 핵심 skill | 역할 |
|---|---|
| `/simon-design-first` | UI 코드 작성 전 강제 진단 (audience/purpose/tone) + 레퍼런스 3-5 + 폰트 선택지. AI slop 방지 게이트 |
| `/plan-design-review` (gstack) | 디자이너 시각의 plan 리뷰 (10-star, 인터랙티브) |
| `/design-shotgun` (gstack) | AI 디자인 N 변형 → 비교 보드 → 피드백 → iterate |
| `/design-html` (gstack) | HTML 시안 생성 |
| `/design-review` (gstack) | 실제 사이트 시각 감사 |
| `/stitch-design-flow` | Google Stitch 용 Safe/Bold/Wild 프롬프트 3 종 생성 |
| `/design-system-page` | design.md → design-system.html + A4 brand-book PDF 자동 생성 |
| `/slides` | zero-dep HTML 슬라이드 (16:9, 3 preview → 선택) — 발표·피치덱 |

### 3. Engineering (개발) — 구현·테스트·디버깅

`founder-context` + `simon-design-first` 가 끝나야 여기 들어옴. TDD 강제, 검증 루프 강제.

| 핵심 skill | 역할 |
|---|---|
| `/simon-tdd` | RED → GREEN → REFACTOR 사이클 강제, 검증 루프 (서버 URL + 테스트 명령) 명시 |
| `/test-gen` | Happy / Sad / Bad / Race / Boundary / Permission / State 7-카테고리 시나리오 |
| `/debug` | 에러 보고서 → root-cause 진단 + fix + reproduction |
| `/refactor` | 구조 개선 |
| `/explain` | 모듈·시스템 walkthrough (entry points, data flow, invariants) |
| `/simon-worktree` | 병렬 작업 시 git worktree 격리 |
| `/phase4-game-orchestrator` | 게임 구현 요청을 과거 일정으로 미루지 않고 엔진·에셋·비용을 확인해 `/vibe` 빌드·검증으로 연결합니다. 초안이나 스토어 게시를 완료로 주장하지 않습니다. |
| `/building-native-ui` | 기존 RN/Expo 구조·SDK를 확인해 네이티브 화면을 구현하고 Android APK/Studio·iOS 검증 범위를 구분합니다. EAS 클라우드 빌드·스토어 제출은 별도 게이트입니다. |
| `/vercel-react` | 기존 React/Next.js·라우터·Vercel 맥락을 확인하고 실측 오류에 맞는 경계·캐시·렌더링만 수정합니다. 프리뷰·운영 배포와 유료 설정은 별도 게이트입니다. |
| `/vue-best-practices` | 기존 Vue/Options·Composition API와 Pinia 규약을 보존하며 반응성 진단·실측 성능 개선·프로젝트 검증을 수행합니다. Vue 버전별 기능과 유료/자동 다운로드 경계를 확인합니다. |
| `/remotion-best-practices` · `/scientific-paper` | 도메인별 best practices (Remotion video/학술논문) |

### 4. DevEx & Platform (플랫폼) — 인프라·툴체인·배포

코드는 됐고, 어떻게 실행하고 배포할지. Vercel / Cloudflare / Fly.io / Railway 선택부터 CI/CD 자동화.

| 핵심 skill | 역할 |
|---|---|
| `/deploy-configurator` | 배포 플랫폼 선택 + CI/CD + custom domain + env 관리 |
| `/app-platform-selector` | 기존 코드·기기 기능·비용 조건에 맞춰 PWA/Hybrid/Native를 비교합니다. Apple 심사 결과를 보장하지 않고 최신 공식 §4.2와 실제 앱 가치를 확인합니다. |
| `/db-selector` | 기존 DB·마이그레이션과 사용량을 먼저 확인하고 공식 가격·무료 한도·초과 과금 조건으로 DB 후보를 비교합니다. 사용자 수만으로 비용을 확정하지 않습니다. |
| `/stack-architect` | 기존 구성과 실측 부하에 맞춰 프론트/백/API·배포 후보를 비교합니다. 사용자 수만으로 서비스·월 비용·Kubernetes를 확정하지 않습니다. |
| `/setup-deploy` (gstack) | `/land-and-deploy` 용 deploy 설정을 CLAUDE.md 에 박음 |
| `/land-and-deploy` (gstack) | 머지 → CI 대기 → 프로덕션 canary 검증 |
| `/ship` (gstack) | 변경 범위·최신 검증·비용/권한을 확인하는 릴리스 흐름. VERSION·push·PR은 프로젝트 규칙과 명시된 승인 범위에서만 수행합니다. |
| `/canary` (gstack) | 프로덕션 헬스 카나리 검증 |
| `/stack-update` | SimonK Stack 본체 + Wiki + gstack + 5 vendored stacks 홀리스틱 최신화 |
| `/multi-terminal-dispatcher` | 중앙 계획·상태·비용을 공유하는 준비된 작업 묶음 실행; 기본은 미리보기 |

### 5. Security & Compliance (보안·법무) — 위협·규제·인증

`simonk` 가 매 sprint 마다 무조건 통과시킴. RLS · authz · 한국 PIPA · GDPR · ad-policy · 결제 ToS.

| 핵심 skill | 역할 |
|---|---|
| `/security-orchestrator` | 4 단계 보안 감사 순차 실행 (checklist → authz → rate-limit → budget cap) |
| `/security-checklist` | RLS·GRANT, 민감 열·웹훅, 사용자/IP 제한, 공급자·앱·사용자 비용 게이트를 증거별로 감사합니다. 유료 호출·운영 변경 없이 미확인 상태를 구분합니다. |
| `/authz-designer` | 기존 서버·DB 권한 경계를 확인해 역할·관계 정책을 설계하거나 교차 테넌트/IDOR를 읽기 전용으로 감사합니다. DDL·운영 권한 변경은 별도 게이트입니다. |
| `/cso` (gstack) | Chief Security Officer 모드 — 종합 보안 결정 |
| `/paid-api-guard` | 결제·SMS 등 종량제 API의 키·서명·남용·비용 경계를 점검합니다. 유료 실호출·메시지 전송·키 회전·결제 설정은 별도 승인입니다. |
| `/keepass-helper` | 시크릿 매니지먼트 |

### 6. Growth & Revenue (그로스·재무) — 사용자·돈·시장

런칭 후 *돈이 들어오나*. AARRR, 결제·구독, 광고, 스토어 출시, exit 전략까지.

| 핵심 skill | 역할 |
|---|---|
| `/aarrr-growth-planner` | Acquisition→Activation→Retention→Referral→Revenue 분석 + ICE 백로그 |
| `/aha-moment-optimizer` | TTFV 단축 + activation 실험 설계 |
| `/payment-integrator` | Stripe / PortOne / RevenueCat / 인앱결제 통합 |
| `/monetization-planner` | 수익 모델 설계 (구독/광고/거래/freemium) |
| `/revenue-scenario-tester` | 80+ 결제 시나리오 통합 테스트 (7 specialized agents) |
| `/store-launcher` | Play Store / App Store 등록 + ASO |
| `/viral-launch` | 채널별 바이럴 플레이북 (인스타 / 한국 커뮤니티 / in-app share) |
| `/pmf-analyzer` | 3-case PMF 예측 (낙관/보통/비관) + Sean Ellis 시뮬레이션 |
| `/exit-strategy-planner` | IPO / M&A / SPAC 로드맵 + Seed→Series 단계별 KPI |

### 7. Knowledge & Memory (지식관리) — 위키·문서·세션·감사

매 세션 끝에 학습이 *어디 저장되나*. wiki + instincts + handoff + perspectives 가 누적 메모리.

| 핵심 skill | 역할 |
|---|---|
| `/simon-handoff` | docs/HANDOFF.md prepend + main 머지까지 자동. 다음 세션이 `git pull` 한 번에 복원 |
| `/perspectives` | 세션 blind-spot 감사 — Core 5 (User/Business/Technical/Security/Future-self) + 세션 특화 N stakeholder, perspectives.md 누적 |
| `/simonk-report` | simonK Phase 6 자동 호출 — `.simonk/reports/<TS>.html` 자체 완결 보고서 + SendUserFile 로 모바일 첨부. 단독 `/simonk-report` 호출도 가능 |
| `/simon-instincts` | `~/.claude/instincts/` 에 cross-project 실수·관용·도구 함정 append |
| `/llm-wiki-builder` | SimonKWiki 페이지 작성 (T-xxx 결정, M-xxx 실수, entities) |
| `/wiki-query` | 위키 인덱스 검색 + [[wikilink]] 인용 답변. 새 결론은 wiki 페이지로 환원 |
| `/wiki-lint` / `/wiki-ingest` | 위키 무결성 + 외부 문서 흡수 |
| `/context-guardian` | 컨텍스트 고갈 예방 + 실측 한도 관리 + 복구 4 mode |
| `/document-release` (gstack) | post-ship README/CHANGELOG/ARCHITECTURE 동기화 |
| `/domain-glossary` | 프로젝트 `CONTEXT.md` 용어집 |
| `/project-context-md` | 프로젝트 `CLAUDE.md` (Claude 검증 도구 명시) 생성 |

### 8. Skill DevOps (자체 도구) — 메타·외부 통합

회사 자체가 쓰는 도구를 만들고 동기화하는 IT 부서. 새 skill 작성·검증, 외부 stack import.

| 핵심 skill | 역할 |
|---|---|
| `/skill-gen-agent` | 새 skill 작성 시 7-단계 검증 파이프라인 (description 점수·네이밍·길이) |
| `/skillify` | 외부 패턴을 simonkstack skill 로 흡수 |
| `/find-skill` | 외부 awesome-claude-skills (26k★) + 내부 INDEX 자동 검색 |
| `/office-docs` | Docx / Xlsx / Pptx / PDF 사무 문서 (Anthropic Big Four) |
| `/web-publisher` | 웹사이트 자동 로그인·폼·업로드 (browse + auth) |
| `/notebooklm-import` | YouTube 자막 + PDF + 웹 → SimonKWiki 페이지 |
| `/gstack-upgrade` | gstack 자체 업그레이드 (install type 자동 감지) |
| `/omc-upgrade` / `/omo-upgrade` / `/openharness-upgrade` / `/opencowork-upgrade` / `/designmd-upgrade` | 각 vendored 외부 stack 단독 최신화 |
| `/update-config` | settings.json·hooks·permissions 관리 |
| `/init` / `/loop` / `/verify` / `/run` | 일반 개발 유틸 |

---

## 📦 같이 들어 있는 앱 — AI Usage Widget

`apps/ai-usage-widget/` — Windows 작업 표시줄 옆에 Claude·Codex·Grok·Antigravity **구독 사용량**(5시간·주간 한도, 리셋까지 남은 시간)을 띄우는 Electron 위젯. 각 공급자의 **공식 CLI 경로만** 쓰고, 조회에 실패하면 가짜 숫자 대신 "미확인"과 마지막 실측 시각을 보여 준다.

새 모델 알림은 공급자 공식 모델 문서와 발표 자료를 별도로 6시간마다 확인한다. 공식 출시가 확인되면 제조사 아이콘 위에 잠깐 말풍선과 배지가 나타나고, 명시된 미래 출시일이 있으면 날짜 기준 `D-n`을 보여 준다. 배지를 누르면 공식 페이지가 열린다. 계정에서 모델을 실제 선택할 수 있는지는 공급자의 플랜·지역·CLI 버전에 따라 다를 수 있다. 최초 실행 시 현재 모델은 알림 없이 기준선으로 기록한다. 자세한 출처와 판정 기준은 [앱 설계 문서](apps/ai-usage-widget/docs/DESIGN.md)를 참고한다.

한도 사용률이 평소보다 빠르게 오르거나 15분 안에 12%p 이상 급증하면 해당 계정을 강조하고 아이콘 위에 8초간 말풍선을 띄운다. 같은 계정의 말풍선은 15분간 반복하지 않으며, 조회 실패·미확인 사용률·한도 리셋은 경고에서 제외한다. 실제 토큰 사용량이 아닌 공급자가 보고한 한도 사용률을 기준으로 한다.

```powershell
# 소스에서 빌드 → 검증 → 사용자 전용 설치 (Windows, node + pnpm + git 필요)
& ".\skills-src\ai-usage-widget-install\scripts\install-widget.ps1"
& ".\skills-src\ai-usage-widget-install\scripts\install-widget.ps1" -Status   # 상태만
```

Claude Code 안에서는 `/ai-usage-widget-install` 또는 "AI 사용량 위젯 설치해줘". 로그인(브라우저·기기 코드)은 위젯 화면에서 사용자가 직접 한다. 타사 로고의 권리는 각 소유자에게 있다 — `NOTICE` 참고.

## /vibe — 메인 진입점, simonk — 스프린트 절차

기존 LLM 세션에서 `/vibe <원하는 결과>`를 사용합니다. 필요한 스킬과
소프트웨어를 고르고, 모델·effort·계정·쿼터·추가 비용·검증을 한 계획으로
관리합니다. `/simonK <task>`도 같은 조정자 아래의 6단계 스프린트 절차입니다.

명확화 → 의존성·리뷰 계획 → 준비된 작업 실행 → 검증·복구 → 범위 내 Git
반영 → 결과 보고. 무조건 병렬 실행하거나 모든 저장소를 자동 push하지 않습니다.
추가 과금 기본값은 $0이며, 미확인 과금이나 사용량을 0으로 간주하지 않습니다.
GUI가 꼭 필요한 일만 내부 vibe-bot 경로로 전달합니다.
Bot 명단의 `active - reported`는 실접속 확인이 아니므로 `/vibe`는 정확한 실측 `active`와 별도 계정·쿼터·Relay 증거가 없으면 발주하지 않습니다.
승인된 Relay 협업 루프에서는 `vibe-bot/scripts/bus_watch.py --watch`로 저장된 상태부터 읽기 전용 감시하고, 작업 발송·운영 변경은 기존 승인 게이트를 따릅니다.

PowerShell의 `simonK`는 슬래시 명령과 다르게 **구조화된 오프라인 계획 전용**입니다.
이전의 `simonK "task"`와 인자 없는 Claude 실행은 차단됩니다.

```powershell
# 기존 세션에 함수를 직접 정의하려면 검토한 지속 clone에서만:
. ./scripts/simonk.ps1
# 배치 스크립트는 binding 실패도 중단하고 종료코드를 전달합니다.
$ErrorActionPreference = 'Stop'
simonK -RequestPath request.json -RuntimePath runtime.json
# exit $LASTEXITCODE  # 배치 파일에서만; 대화형 셸에서는 종료하지 마세요.
```

입력 계약: [vibe 실행 계약](skills-src/vibe/references/orchestration.md).
[스프린트 절차](skills-src/simonk/SKILL.md)와
[다중 실행기](skills-src/multi-terminal-dispatcher/SKILL.md)는 같은 중앙 정본을 소비합니다.
계획 성공·작업 시작·출력 수신·비용 정산·검증 완료는 서로 다릅니다.

### 선택 사항: PowerShell 7 프로필 연결

검토된 실행기·중앙 planner가 일치하는 **지속 일반 clone**을 명시하세요.
임시 linked worktree나 아직 구버전인 main으로 연결하지 않습니다.

```powershell
# 기본은 읽기 전용 미리보기
pwsh -NoProfile -NonInteractive -File scripts/install-simonk-profile.ps1 -RepoRoot 'E:/persistent/SimonK-stack'
# 미리보기와 대상을 확인한 뒤에만 같은 명령에 -Apply 추가
```

기본 대상은 현재 PowerShell의 CurrentUserAllHosts 프로필이며, 절대 경로
`-ProfilePath`로 지정할 수 있습니다. `-Apply`는 정확히 인식된 v1/v2 관리 블록만
교체하고 사용자 코드·인코딩을 보존합니다. 변경 전 파일은 고유 백업으로 남기며,
수정된 블록·중복 표식·불명확한 인코딩은 쓰지 않고 차단합니다. 재적용은 멱등적입니다.

예제 문자열·주석·중첩 함수에 있는 표식은 AST 문맥 검사로 제외합니다.
시작 시 파일의 쓰기·교체를 잠근 상태에서 해시를 확인하고 함수를 로드합니다. 변경·누락·조회 실패 시 로드하지
않고 재설치를 안내합니다. 설치 중 dot-source, 환경변수·gcloud·Team Mode·결제
설정 변경은 없습니다. 기존 환경변수는 그대로 두며 이 명령으로 정리하지 않습니다.
적용 중 다른 편집기를 닫으세요. 마지막 재확인은 외부 편집기 전체를 잠그는 기능이
아닙니다. 복구는 백업·현재 파일을 확인하고 덮어쓰기 권한을 받은 뒤 수동으로 합니다.

이 연결은 전체 스킬 설치, planner 패키지 무결성, 열린 세션의 실행 무결성 또는
5계열 모델 실호출 검증을 대신하지 않습니다. 정식 설치·재설치 checksum은 별도 게이트입니다.

검증: `python -B -m unittest discover -s scripts/tests -p test_install_simonk_profile.py`
(임시 프로필·복제본만 사용, 사용자 프로필 변경 없음).

---

## 🚀 빠른 시작 — 3 가지 설치 모드

### A. Direct install — "내 ~/.claude/ 에만 박아"

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git ~/SimonK-stack
cd ~/SimonK-stack && ./scripts/install.sh
```

이 레거시 설치기는 실행 시점에 가져온 플러그인에 따라 설치 수가 달라지며, 플러그인 소스가 전혀 없을 때만 이 브랜치의 `skills-src/` 137개와 개발용 4개로 폴백합니다. 사용자 홈을 변경하므로 위의 v23 승격 보류 상태에서 후보 검증용으로 실행하지 마세요. SessionStart hook 은 settings.json 에 수동 등록합니다.

### B. Vendor mode — "이 target repo 안에 통째로"

```bash
cd ~/SimonK-stack && ./scripts/setup-repo.sh /path/to/your-project
cd /path/to/your-project && git add .claude && git commit -m "chore(claude): add simon-stack"
```

target repo 의 `.claude/` 에 hook + skill + script 전부 vendor. 다른 사람이 그 repo clone 만 해도 즉시 작동. 가장 자족적.

### C. Bootstrap mode — "2-file drop-in, 매 세션 fresh sync"

```bash
cd ~/SimonK-stack && ./scripts/setup-repo.sh --mode bootstrap /path/to/your-project
```

target repo 에는 hook + settings 만 (2 파일). 매 세션 SimonK-stack clone + 동기화. 가장 가벼움.

### Claude Code 웹 사용

위 B 또는 C 로 setup 한 후 GitHub push → Claude Code 웹에서 해당 repo 열기. SessionStart hook 이 자동 실행되고 simonK 즉시 사용 가능.

---

## 🔁 자동 동기화 — 3-hook 무인 매트릭스

| Hook | 시점 | 동작 | 토큰 비용 |
|---|---|---|---|
| **SessionStart** | 세션 시작 | bootstrap (skill 설치) + upgrade 감지 + auto-pull (clean tree + on main) | 0 |
| **UserPromptSubmit** | 매 사용자 발화 전 | SimonKWiki 5초 인덱스 + 최근 3 log + M/T totals 를 컨텍스트에 inject | ~300-500 |
| **Stop** | LLM 응답 종료 | wiki·instincts dirty 시 자동 commit + push (md/json 변경 위주 필터) | 0 |

**효과**: 사용자가 "wiki", "오답노트" 같은 키워드 안 써도 _LLM 이 스스로_ M-xxx / T-xxx append 가능. 영속화 누락 방지.

**자동 업데이트 출처**:
- SimonK-stack 본체 (this repo)
- SimonKWiki (PRIVATE) — 세션 간 학습
- gstack (upstream) — 실행 파이프라인
- 5 vendored stacks: oh-my-claudecode, oh-my-openagent, OpenHarness, open-cowork, design.md

`/stack-update` 한 명령으로 위 전부 동기화. 개별은 `/<name>-upgrade`.

---

## 🧩 기본 단위 — `skill` 이란?

```
skills-src/<name>/
├── SKILL.md           # 트리거 + 본문 (frontmatter: name, description, tools)
├── evals/cases.json   # 트리거 매칭 테스트 케이스 (최소 2개)
└── (선택) templates/ scripts/ references/
```

- **Description 규칙**: "Use when..." 시작, 한국어+영어 트리거 병기, 400-1024 chars
- **검증**: `python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>` — 0 errors 필수
- **저장소**: `skills-src/` 는 배포용 (Claude Code 로딩 X), `.claude/skills/` 는 개발용 (로딩 O — 토큰 부담 줄이려 분리)
- **새 skill**: 반드시 `/skill-gen-agent` 경유. 직접 SKILL.md 작성 시 description 점수·네이밍·길이 한도 위반 누락

---

## 📚 더 알아보기

| 문서 | 내용 |
|---|---|
| [`.claude/skills/INDEX.md`](.claude/skills/INDEX.md) | 이 브랜치의 소스·개발 스킬 141개 맵 (5플러그인 후보 182개와 구분) |
| [`CLAUDE.md`](CLAUDE.md) | 이 레포에서 작업할 때의 Claude 지침 (검증 도구, 컨벤션, 금기) |
| [`CHANGELOG.md`](CHANGELOG.md) | Keep a Changelog 형식 |
| [`docs/INSTALL.md`](docs/INSTALL.md) | 설치 상세 |
| [`docs/MORNING-START.md`](docs/MORNING-START.md) | 매일 작업 시작 패턴 |
| [`docs/USING-IN-OTHER-REPOS.md`](docs/USING-IN-OTHER-REPOS.md) | 다른 프로젝트에서 사용 |

---

## 🔬 검증 (Verification Loop)

```bash
# 단일 skill 검증
python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>

# 전체 skill CI 검증 (두 소스 루트)
python3 .github/skill-ci/run_ci.py
# Windows에서는 python .github/skill-ci/run_ci.py

# 24-check 통합 테스트
python3 .claude/skills/skill-gen-agent/scripts/tests/run_all.py

# 벤치마크 수집기 회귀 검사 (네트워크 없이 임시 Wiki/cache만 사용)
python3 -m unittest discover -s scripts/tests -p test_fetch_model_benchmarks.py

# /vibe 오프라인 테스트: 상위 스크립트와 tests/를 각각 발견 (실제 모델·Orca 호출 없음)
(cd skills-src/vibe/scripts && PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s . -p 'test_*.py' -q)
(cd skills-src/vibe/scripts && PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q)

# 5-plugin 후보 빌더 회귀 검사 (격리된 임시 Git 입력만 사용)
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s scripts/tests -p test_plugin_bundle.py -q

# Bash 스크립트 문법
for f in scripts/*.sh .claude/hooks/*.sh; do bash -n "$f" && echo "OK: $f"; done
```

5-plugin 후보의 모든 `.sh` 파일은 LF 줄바꿈이어야 합니다. Windows의 Git
`core.autocrlf=true` 체크아웃은 CRLF 스크립트를 만들 수 있으며, 후보 빌드·검증은
이 입력을 차단합니다. 원본 저장소 설정을 바꾸지 말고 격리된 빌드 입력에서
줄바꿈을 확인하세요. 원본 플러그인 작업트리에 Git 무시 캐시가 있으면 빌더의 엄격한 파일 인벤토리와 충돌할 수 있으므로, 고정 커밋을 깨끗한 임시 체크아웃으로 재현하세요. 후보 영수증은 파일 바이트 검증이지 설치·실행 승인서가 아닙니다.

**원칙** (Boris Cherny): Claude 가 *눈으로 확인 가능* 한 검증 명령을 명시. "확인해 주세요" 가 아니라 자신이 실행.

### 벤치마크 수집은 Wiki 갱신이 아닙니다

`scripts/fetch-model-benchmarks.py`는 검토 전 raw 후보만 수집하며 Wiki 본문·날짜·로그와 라우팅 registry를 수정하지 않습니다.
캐시의 `attempted_at`은 조회 시각일 뿐이며 `data_as_of: null`, `validation_status: unverified`, `wiki_updated: false`를 유지합니다.
기존 `fetched_at` 캐시도 검증된 최신 모델 정보로 취급하지 않습니다. 모델 라우팅은 `/vibe`의 중앙 registry와 최신 계정·transport 증거를 사용합니다.

- 종료코드 `0`: **요청한 모든 source**에 형식상 유효한 raw 행이 있습니다. 벤치마크 사실 검증, 전체 leaderboard의 완전한 수집 또는 Wiki 업데이트 성공을 뜻하지 않습니다.
- 종료코드 `2`: 실패·0건·파서 미구현·일부 source 누락·잘못된 행 또는 캐시 저장 실패입니다. 기존 캐시는 유지합니다.
- `--dry-run`: 수집/표시만 하며 파일을 쓰지 않습니다. **네트워크는 사용하므로 오프라인 검사는 위 unittest 명령을 사용합니다.**
- 현재 Vellum/LLM Stats/Aider 파서는 미구현이므로 `--source all`은 incomplete로 종료합니다. 이미 구현된 단일 source만 선택할 수 있지만 결과는 여전히 미검증입니다.
- 외부 Wiki cron은 실패 종료코드도 검사해야 합니다. 이 저장소의 변경은 별도 Wiki 저장소의 cron이나 설치본을 자동 교체하지 않습니다.

---

## 라이선스

MIT — 상세는 [LICENSE](LICENSE). upstream credits (gstack: garrytan, mattpocock skills 등) 동일 라이선스 명시.

---

> *이 README 는 회사 비유로 정리한 요약본. 부서별 전체 skill 표는 [.claude/skills/INDEX.md](.claude/skills/INDEX.md), 자율 진입점 protocol 은 [`skills-src/simonk/`](skills-src/simonk/) 를 보세요.*
