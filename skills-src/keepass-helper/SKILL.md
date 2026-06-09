---
name: keepass-helper
description: "Use when the user invokes \"keepass\", \"keepassxc\", \"keepass-inject\", \"/keepass-helper\", \"API 키 자동 inject\", \"vault 키\", or \"simonk-keepass-inject\". Produces (1) KeePassXC vault status check (path + CLI presence), (2) one-time master password prompt + auto inject for all known entries (Zotero/Anthropic/OpenAI/Gemini/GitHub), (3) env var diagnosis (which set/missing), (4) SecureString persistence option for repeat-sessions. Master password lives in current session memory only — never saved to disk or env."
allowed-tools: Read, Bash
version: 1.0.0
author: simon-stack
---

# keepass-helper

KeePassXC vault에서 API key 자동 inject. **첫 1회 master password 입력** + 그 session 안에서 모든 known entry 환경변수 자동 사용.

## 발동 조건

다음 트리거 중 하나로 호출:
- `keepass`, `keepassxc`, `keepass-inject`, `/keepass-helper`
- "API 키 자동 inject", "vault 키 가져와"
- `simonk-keepass-inject` (PowerShell helper)

## 사용 흐름 (3 단계)

### Step 1. PowerShell session 시작 시 1회 호출

```powershell
# 직접 호출
. "C:\Coding\Harrness Eng\SimonK-stack\scripts\keepass-inject.ps1"
Invoke-KeepassInject

# 또는 alias
keepass-inject
```

→ master password prompt → 입력 → 5 known entry 자동 inject.

### Step 2. 출력 확인

```
[keepass] inject ZOTERO_API_KEY = 4ooaJcSR...zh9o
[keepass] inject ANTHROPIC_API_KEY = sk-ant-...xxxx
[keepass] inject GH_TOKEN,GITHUB_TOKEN = ghp_xxxx...xxxx
[keepass] 3 entries injected to current session
```

### Step 3. 그 session 안에서 자동 사용

```powershell
claude                                       # → ZOTERO_API_KEY 자동 inherit
simonK <task>                                # → 모든 inject env var 사용 가능
graphify extract . --backend claude          # → ANTHROPIC_API_KEY 자동
```

## Known entry 매핑

KeePassXC entry title → 환경변수 자동 inject:

| KeePassXC Entry | 환경변수 |
|---|---|
| `Zotero API Key` | `ZOTERO_API_KEY` |
| `Anthropic API Key` | `ANTHROPIC_API_KEY` |
| `OpenAI API Key` | `OPENAI_API_KEY` |
| `Gemini API Key` | `GEMINI_API_KEY` + `GOOGLE_API_KEY` |
| `GitHub PAT` | `GH_TOKEN` + `GITHUB_TOKEN` |

→ KeePassXC vault entry title을 *정확히* 위 이름으로 만들면 자동 매핑. 다른 entry 추가는 `scripts/keepass-inject.ps1` 의 `$KeepassEntries` hashtable 갱신.

## 단일 entry inject (선택)

```powershell
Invoke-KeepassInject -Entry "Zotero API Key"   # ZOTERO_API_KEY만
```

## 보안

- ❌ Master password **절대 file/registry/env에 저장 X**
- ✅ 현재 session 메모리만 (`SecureString` + `BSTR` 즉시 release)
- ✅ Environment variable = *current process scope* (자식 process inherit, 새 session에는 X — 매 session 1회 재호출)
- ✅ `keepassxc-cli stdin pipe` (master password CLI argument 노출 X)

## Default vault 위치

`C:\Coding\암호.kdbx`

다른 vault 사용 시:
```powershell
$env:SIMONK_KEEPASS_VAULT = 'C:\path\to\other.kdbx'
Invoke-KeepassInject
```

## simonK 자율 하네스 통합 (현재 X)

본 skill은 *사용자 명시 호출*만 (master password prompt이라 자동 X). 매 simonK 호출 시 자동 inject 원하면:
- 옵션 A: `simonk.ps1`에 본 함수 통합 + 매 호출 prompt (번거로움)
- 옵션 B: Windows Credential Manager에 master password 저장 (보안 trade-off)
- 옵션 C: KeePassXC Key File 사용 (master password 없이 file unlock)

→ 현재는 *사용자 명시 호출* (가장 안전).

## 교차참조

- `scripts/keepass-inject.ps1` — base PowerShell script
- `SimonKWiki/wiki/entities/tools/bitwarden.md` — KeePassXC 도구 페이지 (사용자 결정 history)
- `scripts/simonk.ps1` — simonK 진입점 (현재 keepass 자동 호출 X)
