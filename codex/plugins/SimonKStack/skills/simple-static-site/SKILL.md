---
name: simple-static-site
description: >
  Use when the user wants a single-file static page made fast — triggers "한 파일 사이트", "동아리 페이지", "랜딩 한 장", "정적 페이지 만들어", "one file site", "single page", "club page", "static landing", or /simple-static-site. Produces 한 개의 self-contained HTML 파일 (인라인 CSS, zero build, 외부 의존 없음) → 로컬에서 파일 열기로 미리보기 → 무계정 공유(GitHub Pages / Netlify Drop) 안내. 반응형 + 접근성(큰 글씨·대비·키보드) 기본. 비개발자·라이트 용도. Different from /web-publisher (기존 사이트 폼 자동화), /design-html (디자인 시스템 기반 프로덕션 페이지), /deploy-configurator (CI/CD·호스팅 인프라). This is the no-build, no-account, one-file path.
version: 1.0.0
author: simon-stack
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# /simple-static-site

한 개의 self-contained HTML 파일을 만든다. 빌드 단계, npm, 프레임워크, 외부 CDN 없이 그 파일 하나만 더블클릭하면 브라우저에서 열린다. 비개발자도 다룰 수 있는 가장 가벼운 경로다. 동아리 소개, 행사 안내, 한 장짜리 랜딩, 프로필 카드처럼 "정적 한 장"이면 충분한 경우에 쓴다.

## 언제 쓰나

| 트리거 | 예시 |
|---|---|
| 한국어 | "한 파일 사이트", "동아리 페이지 만들어", "랜딩 한 장", "정적 페이지 만들어 줘", "소개 페이지 한 장" |
| 영어 | "one file site", "single page", "club page", "static landing" |
| Slash | `/simple-static-site` |

## 경계 (다른 skill 과 구분)

| skill | 무엇이 다른가 |
|---|---|
| `web-publisher` | 기존 사이트에 로그인·폼 자동 작성. 이 skill 은 새 파일을 만든다. |
| `design-html` | 확정된 디자인 시스템 기반 프로덕션 페이지. 이 skill 은 build-free 라이트 한 장. |
| `design-consultation` | 디자인 방향 진단·레퍼런스 추천. 톤을 정해야 하면 그쪽 먼저. |
| `deploy-configurator` | CI/CD·커스텀 도메인·모니터링. 이 skill 의 공유는 무계정 드래그&드롭 수준. |

⚠️ 폼 제출·로그인·DB·서버 로직이 필요하면 이 skill 이 아니다. 정적 한 장만 다룬다.

## 핵심 원칙

- **한 파일**: 모든 CSS 는 `<style>` 인라인. JS 는 토글 같은 최소한만, 역시 인라인. 외부 요청 0개 → 오프라인에서도 열림.
- **zero build**: `node`/`python` 없이도 파일 열기만으로 동작. 생성 스크립트만 Node 를 쓴다(결과물은 순수 HTML).
- **반응형 기본**: `max-width` 컨테이너 + 모바일 우선. RN/Expo 웹뷰나 모바일 브라우저에서도 깨지지 않는다.
- **접근성 기본**: 본문 18px↑, 대비 AA↑, `lang` 속성, 시맨틱 태그, 포커스 링 유지, 큰 글씨 토글 제공.
- **AI slop 금지**: 이모지 장식, 과한 그라데이션, 4색 이상 금지. accent + text + bg 3색 이내.

## 단계

1. **진단 (3가지만 묻는다)** — `AskUserQuestion` 으로 한 번에.
   - 누가/무엇: 페이지 종류 (동아리·행사·프로필·랜딩·공지 중)
   - 톤: minimal / warm / bold
   - 큰 글씨 모드 기본 ON 여부 (시니어·접근성 우선이면 ON)
   사용자가 "알아서" 라고 하면 종류=랜딩, 톤=minimal, 큰글씨=OFF 로 진행.

2. **콘텐츠 수집** — 제목, 한 줄 소개, 본문 섹션 2~4개, 연락/링크 1개. 비어 있으면 placeholder 로 채우되 `[여기에 ...]` 형태로 표시해 사용자가 바로 찾도록 한다.

3. **생성** — 스크립트로 단일 HTML 작성.
   ```bash
   node "{skill_dir}/scripts/generate.mjs" \
     --out "<절대경로>/index.html" \
     --title "동아리 이름" \
     --tagline "한 줄 소개" \
     --tone minimal \
     --largeText false \
     --content "{skill_dir}/templates/content.example.json"
   ```
   - `--content` 는 섹션 배열 JSON (아래 스키마). 생략하면 종류별 기본 섹션이 들어간다.
   - 스크립트는 입력만으로 결정론적 출력(같은 입력 → 같은 파일). 네트워크 호출 없음.

4. **로컬 미리보기 (파일 열기)** — 서버 불필요. 절대경로로 기본 브라우저에서 연다.
   ```bash
   # Windows
   node "{skill_dir}/scripts/preview.mjs" "<절대경로>/index.html"
   ```
   `preview.mjs` 는 OS 를 감지해 Windows=`start`, macOS=`open`, Linux=`xdg-open` 으로 파일 URL 을 연다. 실패하면 `file://<절대경로>` 를 그대로 출력하니 사용자가 직접 붙여 넣으면 된다.

5. **검증** — `scripts/check.mjs` 로 산출물 자가 점검 (아래 표 항목). 통과 못 한 항목은 이름으로 보고하고 고친다.

6. **무계정 공유 안내** — 계정/CLI 없이 가능한 두 경로를 사용자에게 제시한다(자동 업로드는 하지 않음, 사용자가 직접 드래그).

## content JSON 스키마

```json
{
  "sections": [
    { "heading": "우리는", "body": "동아리 한 줄 설명." },
    { "heading": "활동", "body": "정기 모임, 프로젝트, 발표회." },
    { "heading": "함께해요", "body": "매주 수요일 19시. 누구나 환영." }
  ],
  "cta": { "label": "신청 폼 열기", "href": "https://example.com/apply" }
}
```

- `cta.href` 가 없으면 버튼을 그린다(`mailto:` 등). 외부 폼이 필요하면 그 URL 만 넣는다 — 이 skill 은 폼을 만들지 않는다.
- 시크릿·API 키는 절대 넣지 않는다. 정적 파일은 누구나 소스를 본다.

## 톤 프리셋 (3색 이내)

| 톤 | bg | text | accent | 용도 |
|---|---|---|---|---|
| minimal | `#fbfbfd` | `#1d1d22` | `#3b5bdb` | 기본·프로페셔널 |
| warm | `#fdfaf6` | `#2a2420` | `#c2410c` | 동아리·커뮤니티 |
| bold | `#0f1115` | `#f2f3f5` | `#22d3ee` | 행사·런칭(다크) |

폰트: 한국어 본문은 시스템 폰트 스택(`-apple-system, "Segoe UI", "Malgun Gothic", sans-serif`)으로 외부 요청 0 유지. 사용자가 명시적으로 웹폰트를 원하면 Pretendard CDN 한 줄을 옵션으로 안내(그 경우 오프라인 동작은 포기됨을 고지).

## 검증 체크리스트 (`check.mjs` 가 검사)

- [ ] 단일 파일 — `<link rel=stylesheet>`, 외부 `<script src>`, `import` 없음 (웹폰트 옵션 선택 시 1개만 허용)
- [ ] `<!doctype html>` + `<html lang="ko">` + `<meta charset>` + `<meta name="viewport">`
- [ ] `<title>` 비어있지 않음, `<h1>` 정확히 1개
- [ ] 본문 글자 ≥ 18px, 컨테이너 `max-width` 존재(반응형)
- [ ] accent/text/bg 총 3색 이내, 그라데이션·glassmorphism 없음
- [ ] placeholder `[여기에 ...]` 가 남아 있으면 경고로 보고

## 무계정 공유 (사용자가 직접, 자동 업로드 금지)

| 방법 | 절차 | 비고 |
|---|---|---|
| Netlify Drop | https://app.netlify.com/drop 접속 → `index.html`(또는 폴더) 드래그 | 계정 없이 즉시 URL. 가장 빠름 |
| GitHub Pages | repo 에 `index.html` push → Settings ▸ Pages ▸ branch `main` ▸ Save | GitHub 계정만 있으면 무료·영구 |
| 파일 직접 전달 | HTML 파일을 메신저·이메일로 전송 | 받는 사람이 더블클릭으로 열람 |

호스팅 인프라·CI·커스텀 도메인이 필요해지면 `deploy-configurator` 로 넘긴다.

## 외부 의존

- 생성/미리보기/검증 스크립트: Node 18+ (표준 라이브러리만, npm 설치 불필요).
- 결과물 HTML: 의존 없음(웹폰트 옵션 미선택 시).

## 실패 시

- 스크립트 인자 누락: 어떤 인자가 빠졌는지 이름으로 출력하고 중단.
- `preview.mjs` 가 브라우저를 못 열면 `file://` 경로를 출력 — 수동으로 열도록 안내.
- `check.mjs` 가 실패 항목을 나열하면 해당 부분만 고친 뒤 재검사.

## Related Skills

- `design-html` — 디자인 시스템 기반 프로덕션 페이지로 격상할 때
- `design-consultation` — 톤·레퍼런스·폰트 방향을 먼저 잡을 때
- `deploy-configurator` — 정식 호스팅·CI/CD·도메인이 필요해질 때
