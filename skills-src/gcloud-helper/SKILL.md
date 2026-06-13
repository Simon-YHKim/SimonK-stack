---
name: gcloud-helper
description: "Use when the user invokes \"gcloud\", \"/gcloud-helper\", \"gcloud auth\", \"ADC\", \"BigQuery 인증\", \"Vertex AI 인증\", or \"simonk-gcloud-check\". Produces auth status diagnosis + ghost project auto-fix + env vars inject (GOOGLE_CLOUD_PROJECT + GOOGLE_APPLICATION_CREDENTIALS) + browser OAuth one-liner if needed. Auto-called by simonK harness silent if OK."
allowed-tools: Read, Bash
version: 1.0.0
author: simon-stack
---

# gcloud-helper

Google Cloud SDK 자동 진단 + 인증 안내 + 환경 자동 inject. simonK PowerShell 하네스가 *자동 호출* (silent if OK). 사용자 인터랙션 = **첫 1회 browser OAuth만**.

## 발동 조건

다음 트리거 중 하나로 호출:
- `gcloud`, `google cloud`, `/gcloud-helper`
- "gcloud auth", "ADC", "Application Default Credentials"
- "BigQuery 인증", "Vertex AI 인증"
- "구글 클라우드 설정", "gcloud 자동 설정"
- `simonk-gcloud-check` (PowerShell function 직접 호출)

또한 simonK harness가 매 호출 시 자동 — `scripts/simonk.ps1`이 `Invoke-GcloudBootstrap -Silent` 호출.

## 5-Step 자동 진단

### Step 1. gcloud CLI 존재 확인

```powershell
Get-Command gcloud -ErrorAction SilentlyContinue
```

없으면 안내:
```
winget install Google.CloudSDK --silent
```

### Step 2. 인증 상태 (gcloud auth list)

```powershell
gcloud auth list --filter=status:ACTIVE --format="value(account)"
```

**인증 없음** → 사용자에게 1줄 안내 (자동 browser 호출 X — noise 방지):
```
gcloud auth login                               # 1회 browser OAuth (사용자가 Google 로그인 + 권한 승인)
gcloud auth application-default login           # ADC (Python 라이브러리용)
```

**인증 있음** → 활성 계정 출력 (silent 아닌 경우).

### Step 3. 활성 project 자동 fix

```powershell
$project = gcloud config get-value project
$userProjects = gcloud projects list --format="value(projectId)"
```

**유령 project** (config에 있지만 실존 X — 예: `simonk-personal` quota 초과) → 자동 fallback:
1. `eject-button` 있으면 자동 set
2. 없으면 첫 번째 user project

→ `GOOGLE_CLOUD_PROJECT` + `GCLOUD_PROJECT` 환경변수 자동 inject (현재 session).

### Step 4. ADC (Application Default Credentials) verify

```powershell
$adcPath = "$env:APPDATA\gcloud\application_default_credentials.json"
Test-Path $adcPath
```

**ADC 있음** → `GOOGLE_APPLICATION_CREDENTIALS` 환경변수 자동 inject.
**ADC 없음** → 안내:
```
gcloud auth application-default login
```

### Step 5. Claude session에 env 자동 inject

simonK 호출 시 silent 자동 — 사용자는 *모름*. 단 BigQuery / Vertex AI / Drive API 등 호출 시 *자동 인증*.

## 직접 호출 (PowerShell)

```powershell
# 진단만 (출력)
. "E:\Coding Infra\Harrness Eng\SimonK-stack\scripts\gcloud-bootstrap.ps1"
Invoke-GcloudBootstrap

# 자동 + silent (인증 OK 시 출력 없음)
Invoke-GcloudBootstrap -Silent

# simonk profile loaded 후 (전역 helper)
simonk-gcloud-check
```

## 처음 사용자 — 1회 OAuth flow (1분)

**단 1번만**:
1. `gcloud auth login` 실행
2. 브라우저 자동 열림 → Google 계정 선택 → "허용"
3. PowerShell에 `You are now logged in as [<email>]` 표시
4. `gcloud auth application-default login` 실행 (ADC, 선택)
5. 브라우저 자동 → 동일 flow

이후 *영원히* 자동 — OAuth refresh token이 자동 갱신.

## 보안

- ❌ SimonK-stack은 *비밀번호 절대 저장 X*
- ❌ Google ID/PW 직접 받기 X (OAuth2 정책)
- ✅ gcloud 표준 credentials 위치 (`~/.config/gcloud/`)
- ✅ ADC 표준 위치 (`%APPDATA%\gcloud\application_default_credentials.json`)
- ✅ 환경변수는 *현재 session*만 (영구 set X — 보안)

## 활용 시나리오

### Phase 3 (6/15~6/30) — Workspace 통합

- NotebookLM (browser automation은 별도) — gcloud는 옵션
- Google Drive 동기 (gsutil)
- Calendar API · Sheets API · Docs API

### Phase 4 (7월~9월) — R&D 클라우드 단계

- **Vertex AI** (Gemini Pro Code Assist, custom model) — ADC 필수
- **BigQuery** (도메인 로그 분석) — `bq query` + ADC
- **GCS** (모델 artifact 저장) — `gsutil cp`

### Phase 6 (27Y Q1~) — Simon-ohmo

- 폐쇄망 운영 — gcloud 호출 X (Ollama 로컬)
- 단 *백업/동기*는 GCS 사용 가능

## 자동화 통합

| Layer | 위치 | 동작 |
|---|---|---|
| **1** | `scripts/gcloud-bootstrap.ps1` | PowerShell base script |
| **2** | `scripts/simonk.ps1` | simonK 호출 시 자동 (silent if OK) |
| **3** | 본 skill (`gcloud-helper`) | Claude Code session 안에서 명시 호출 |

## 교차참조

- `scripts/gcloud-bootstrap.ps1` — base script
- `scripts/simonk.ps1` — 자동 통합
- `SimonKWiki/wiki/entities/tools/gcloud-helper.md` — wiki 도구 페이지
- `SimonKWiki/wiki/protocols/operations-manual.md § 4` — 운영 SOP
