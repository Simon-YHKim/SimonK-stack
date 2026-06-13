---
name: notebooklm-import
description: >
  Use when Simon wants to pull an external source (YouTube video, web article, or PDF) into the SimonKWiki vault — triggers "비디오 자막 가져와", "유튜브 자막 위키에", "이 영상 정리해줘", "PDF 위키에 넣어줘", "이 글 클리핑해서 인제스트", "import this video transcript", "pdf to knowledge base", "clip this article into the wiki". Produces a raw/ source file (subtitle text via yt-dlp, article body via defuddle, or PDF text via pdftotext/pypdf) landed under raw/transcripts|clipped|documents with proper frontmatter, then hands off to wiki-ingest for the reflective compile into wiki/sources/. For headless runs where wiki-ingest's 4-question gate cannot be answered, the raw file is tagged status: needs-reflection and left for a later interactive pass. Different from wiki-ingest (compiles already-saved raw/ files), defuddle (single-page extract, no wiki routing), and notebooklm (Google NotebookLM cloud API).
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
compatibility:
  - claude-code
---

# notebooklm-import

외부 소스(YouTube 자막 · 웹 기사 · PDF)를 추출해 **SimonKWiki `raw/`** 에 표준 frontmatter로 떨군 뒤 `wiki-ingest` 로 넘기는 인제스트 파이프라인. NotebookLM의 "소스 추가" 단계를 로컬·오프라인으로 재현한다 — 자막/본문을 텍스트로 뽑는 것까지가 이 skill 의 책임이고, 사유(reflection)·`wiki/` 반영은 `wiki-ingest` 가 맡는다.

## When to use / boundaries

| 상황 | 이 skill | 다른 skill |
|---|---|---|
| YouTube/웹/PDF 소스를 vault 에 넣고 싶다 | ✅ notebooklm-import | |
| 이미 `raw/` 에 저장된 글을 위키에 컴파일 | | `wiki-ingest` |
| URL 한 페이지를 그냥 읽고 분석(저장 X) | | `defuddle` |
| Google NotebookLM 노트북·팟캐스트·퀴즈 생성 | | `notebooklm` |
| 위키 정합성 점검 | | `wiki-lint` |

**경계 원칙**
- `raw/` 는 **불변(immutable)** — 이 skill 은 `raw/` 에 **새 파일을 추가만** 하고, 기존 파일은 절대 수정/삭제하지 않는다.
- `wiki/` 페이지 생성·`index.md`·`log.md` 갱신은 이 skill 이 **직접 하지 않는다.** `wiki-ingest` 에 위임한다(중복 책임 방지).
- 저작권/유료 콘텐츠 전문(全文) 대량 복제는 하지 않는다 — 자막·본문은 요약·인용 목적의 raw 보관까지.

## Vault 경로 (정본)

```
VAULT="E:/Coding Infra/obsidian/SimonKWiki"
```

| 소스 타입 | raw/ 착지 폴더 | 파일명 규칙 |
|---|---|---|
| YouTube 자막 | `raw/transcripts/` | `YYYY-MM-DD-youtube-<slug>.md` |
| 웹 기사 | `raw/clipped/` | `YYYY-MM-DD-<domain>-<slug>.md` |
| PDF/논문 | `raw/documents/` 또는 `raw/clipped/papers/` | `YYYY-MM-DD-<slug>.md` |

`wiki-ingest` 가 뒤이어 `wiki/sources/YYYY-MM-DD-youtube-<slug>.md` 를 만든다 (기존 예: `2026-06-13-youtube-loop-engineering.md`).

## 선행 체크 (precheck)

```bash
VAULT="E:/Coding Infra/obsidian/SimonKWiki"
test -d "$VAULT/raw" && echo "VAULT_OK" || { echo "VAULT 없음 — 경로 확인"; exit 1; }

# 도구 가용성 (없으면 설치 안내, 막지 않음)
( yt-dlp --version || python -m yt_dlp --version ) 2>/dev/null && echo "ytdlp_OK"   || echo "ytdlp_MISSING"
command -v defuddle  >/dev/null 2>&1 && echo "defuddle_OK"  || echo "defuddle_MISSING"
command -v pdftotext >/dev/null 2>&1 && echo "pdftotext_OK" || echo "pdftotext_MISSING"
command -v ffmpeg    >/dev/null 2>&1 && echo "ffmpeg_OK"    || echo "ffmpeg_MISSING (srt 변환 시 필요)"
```

설치 (없을 때만):
```bash
python -m pip install -U yt-dlp        # YouTube 자막 — pip 설치가 최신 유지에 유리
npm  install -g defuddle               # 웹 본문 추출 (이미 설치돼 있음)
# pdftotext = poppler-utils, pypdf/pdfplumber = pip — 이 환경엔 이미 존재
```

> 이 환경 확인됨(2026-06): `defuddle` ✅, `pdftotext 4.00` ✅, `pypdf 6.13` ✅, `pdfplumber 0.11.9` ✅, **`yt-dlp` 미설치** → YouTube 작업 전 `pip install -U yt-dlp` 먼저.

## Workflow

### 1. 소스 타입 분기

```
입력 분석
├─ youtube.com / youtu.be URL        → 2A. yt-dlp 자막
├─ http(s) 일반 웹페이지 (.md 아님)   → 2B. defuddle 본문
├─ 로컬/원격 .pdf                     → 2C. PDF 텍스트
└─ .md URL                            → defuddle 불필요, WebFetch 로 직접
```

### 2A. YouTube 자막 추출 (yt-dlp)

자막만 받고 영상은 **다운로드하지 않는다**(`--skip-download`). 수동 자막 우선, 없으면 자동 생성 자막(`--write-auto-subs`). 언어는 한국어+영어 우선.

```bash
URL="https://www.youtube.com/watch?v=XXXX"
OUT="$VAULT/raw/transcripts/_tmp"          # 임시 추출 위치
yt-dlp \
  --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "ko,en,en-orig" \
  --sub-format "vtt/srt/best" \
  --convert-subs srt \
  --restrict-filenames \
  -o "$OUT/%(upload_date>%Y-%m-%d)s-%(title)s.%(ext)s" \
  "$URL"
# pip 설치본은 `python -m yt_dlp ...` 로 호출
```

| 플래그 | 역할 |
|---|---|
| `--skip-download` | 영상 본체 스킵, 자막만 |
| `--write-subs` | 업로더 제공 수동 자막 |
| `--write-auto-subs` | 없을 때 자동 생성 자막 폴백 |
| `--sub-langs "ko,en,en-orig"` | 한·영 우선 (콤마=다중, `en-orig`=원어 자동자막) |
| `--convert-subs srt` | srt 로 통일 (ffmpeg 필요). ffmpeg 없으면 `--sub-format vtt` 로 두고 아래 텍스트화 |
| `--restrict-filenames` | 공백/특수문자 제거(Windows 안전) |

추출된 `.srt`/`.vtt` 에서 **타임코드·번호·중복라인 제거**해 순수 텍스트로:
```bash
# srt → 평문 (타임코드/인덱스/빈줄 제거, 연속 중복 제거)
grep -vE '^[0-9]+$|-->|^\s*$' "$OUT"/*.srt | awk '!seen[$0]++' > "$OUT/clean.txt"
# vtt 인 경우: WEBVTT 헤더·cue setting 도 같이 제거
grep -vE '^WEBVTT|^[0-9]+$|-->|^\s*$|^Kind:|^Language:' "$OUT"/*.vtt | awk '!seen[$0]++' > "$OUT/clean.txt"
```
> 자동자막(auto-subs)은 같은 줄이 롤업되며 반복된다 — `awk '!seen[$0]++'` 의 중복 제거가 핵심. 빠지면 raw 가 3~4배로 부풀고 wiki-ingest 가 오판한다.

### 2B. 웹 기사 본문 (defuddle)

```bash
defuddle parse "https://example.com/post" --md -o "$VAULT/raw/clipped/_tmp.md"
DOMAIN=$(defuddle parse "https://example.com/post" -p domain)
TITLE=$(defuddle parse "https://example.com/post" -p title)
```
- `.md` 로 끝나는 URL 은 defuddle 건너뛰고 WebFetch 로 직접 받는다(이미 마크다운).
- 본문이 비었거나 페이월/JS 렌더면 WebSearch 로 캐시·요약 확보 후 사용자에게 보고.

### 2C. PDF 텍스트 추출

레이아웃 단순 → `pdftotext`, 표/다단 → `pdfplumber`:
```bash
# 1순위: pdftotext (-layout 로 단 구조 보존)
pdftotext -layout "paper.pdf" "$VAULT/raw/documents/_tmp.txt"

# 깨지면 2순위: pypdf (텍스트 레이어)
python - <<'PY'
from pypdf import PdfReader
t = "\n".join((p.extract_text() or "") for p in PdfReader("paper.pdf").pages)
open(r"E:/Coding Infra/obsidian/SimonKWiki/raw/documents/_tmp.txt","w",encoding="utf-8").write(t)
PY

# 표·다단 정밀 추출이 필요하면 3순위: pdfplumber
```
> 스캔 PDF(이미지)는 텍스트 레이어가 없어 위 셋 모두 빈 결과. 그 경우 OCR 이 필요하므로 막혔다고 사용자에게 보고하고 결정받는다(자동 OCR 미수행).

### 3. raw/ 파일로 정착 (frontmatter 부착)

추출 텍스트를 표준 frontmatter 와 함께 `raw/` 의 알맞은 폴더에 **새 파일로 Write**. `wiki/CLAUDE.md` 규칙 5 의 "최소 4요소"(한 줄 요약·핵심 3개·출처/작성일·연결 도메인)를 본문 머리에 남긴다.

```markdown
---
title: "YouTube — <영상 제목>"
source_type: youtube          # youtube | web | pdf
source_url: "https://www.youtube.com/watch?v=XXXX"
captured: 2026-06-13          # KST: Get-Date -Format 'yyyy-MM-dd'
ingested: false               # wiki-ingest 가 컴파일하면 true 로
status: needs-reflection      # 헤드리스: 4질문 미응답 표식 / 인터랙티브면 생략
tags: [youtube, transcript]
---

> **한 줄 요약**: <추출 직후 1문장>
> **핵심 3**: 1) … 2) … 3) …
> **출처**: <URL> / captured 2026-06-13
> **연결**: <관련 프로젝트·업무·도메인>

<정제된 자막/본문/PDF 텍스트 전문>
```

임시 파일 정리:
```bash
rm -rf "$VAULT/raw/transcripts/_tmp" "$VAULT/raw/clipped/_tmp.md" "$VAULT/raw/documents/_tmp.txt"
```
> `ingested: false` / `status: needs-reflection` 는 `wiki-log.md` 의 "아직 인제스트 안 됨" 판별 키다. raw 파일명이 `wiki/log.md` 에 없거나 frontmatter `ingested: false` 면 미인제스트로 본다.

### 4. wiki-ingest 핸드오프

raw 정착이 끝나면 **wiki-ingest 가 이어받는다.** wiki-ingest 는 **인터랙티브**다 — Phase 1 에서 4개 회고 질문(왜 캡처? 관심사 연결? 다른 점? 뭘 해볼까?)을 던지고 사용자 답을 받아야 Phase 2(컴파일)로 간다.

- **인터랙티브 세션**: 곧바로 `wiki-ingest` 호출 → 4질문 답변 → `wiki/sources/` 생성 + entity/concept 갱신 + `index.md`/`log.md` 반영.
- **헤드리스/야간 세션**(질문에 답할 사람 없음): wiki-ingest 의 게이트를 강제로 넘기지 말 것. raw 파일을 `status: needs-reflection` 로 남겨두고, **나중에 인터랙티브 패스에서 일괄 인제스트**하도록 보고만 한다. (헤드리스에서 회고를 임의 창작하면 vault 톤·권위 규칙 위반.)

```
needs-reflection 큐 확인:
  grep -rl "status: needs-reflection" "$VAULT/raw"
```

## 검증 (verification)

```bash
VAULT="E:/Coding Infra/obsidian/SimonKWiki"

# 1) raw 파일이 생겼고 비어있지 않은가
NEW=$(ls -t "$VAULT/raw/transcripts"/*.md 2>/dev/null | head -1)
test -s "$NEW" && echo "raw OK: $NEW ($(wc -l < "$NEW") lines)" || echo "raw 비었음/실패"

# 2) frontmatter 4키 존재
grep -qE '^source_url:'   "$NEW" && grep -qE '^source_type:' "$NEW" \
  && grep -qE '^captured:' "$NEW" && grep -qE '^ingested:' "$NEW" \
  && echo "frontmatter OK" || echo "frontmatter 누락"

# 3) 자동자막 중복이 제거됐는가 (동일 라인 5회 이상이면 정제 실패)
sort "$NEW" | uniq -c | sort -rn | awk '$1>=5{print; f=1} END{if(f)print "⚠ 중복 잔존"; else print "dedup OK"}'

# 4) (인터랙티브 인제스트 후) wiki/sources 페이지 + log 기록 확인
ls -t "$VAULT/wiki/sources"/*.md | head -1
grep -c "ingest" "$VAULT/wiki/log.md"
```

체크리스트:
- [ ] yt-dlp/defuddle/pdftotext 중 해당 도구 가용 확인
- [ ] `--skip-download` 로 영상 본체 미다운로드
- [ ] 자동자막 타임코드·중복 제거 완료
- [ ] raw/ 에 **새 파일만** 추가(기존 불변)
- [ ] frontmatter: `source_url`·`source_type`·`captured`·`ingested:false`
- [ ] 인터랙티브면 wiki-ingest 4질문 통과 / 헤드리스면 `needs-reflection` 큐로
- [ ] `wiki/sources/` 생성·`index.md`·`log.md` 갱신은 wiki-ingest 가 수행

## Anti-patterns

- ❌ `raw/` 기존 파일 수정/덮어쓰기 → 불변성(규칙 1) 위반. **새 파일만 추가**.
- ❌ `--skip-download` 빼서 영상 본체까지 받음 → 디스크·시간 낭비.
- ❌ 자동자막 중복 라인 미제거 → raw 3~4배 부풀고 ingest 오판.
- ❌ json3/ttml 자막 포맷 사용 → 파싱 깨짐. **vtt 또는 srt 만**.
- ❌ 헤드리스에서 wiki-ingest 4질문을 임의 답변으로 채움 → 사용자 권위 규칙 위반. `needs-reflection` 로 보류.
- ❌ 이 skill 이 직접 `wiki/sources` 생성·`index.md` 수정 → wiki-ingest 와 책임 중복·이중 기록.
- ❌ 스캔 PDF(이미지)를 OCR 없이 빈 텍스트로 저장 → 막혔으면 보고하고 결정받기.
- ❌ 페이월 기사 전문 무단 대량 복제 → 인용·요약 목적 범위 유지.

## Related skills

- `wiki-ingest` — raw/ → wiki/ 컴파일(4질문 게이트). 이 skill 의 **다음 단계**.
- `defuddle` — 단일 웹페이지 본문 추출(저장·라우팅 없음). 2B 단계에서 호출.
- `notebooklm` — Google NotebookLM 클라우드 API(노트북·팟캐스트·퀴즈).
- `wiki-lint` — 인제스트 후 정합성 점검(broken wikilink·orphan·stale).
- `llm-wiki-builder` — 새 vault 초기화(3-layer Karpathy).
