#!/usr/bin/env node
/**
 * generate.mjs — 단일 self-contained HTML 정적 페이지 생성기.
 *
 * 결정론: 같은 입력 → 같은 출력. 네트워크 호출 없음. 외부 의존 없음(Node 표준 라이브러리만).
 * 결과물은 순수 HTML 한 파일(인라인 CSS, 외부 요청 0). 더블클릭으로 열린다.
 *
 * 사용:
 *   node generate.mjs --out <path> --title <t> [--tagline <s>]
 *        [--tone minimal|warm|bold] [--largeText true|false]
 *        [--content <content.json>] [--kind landing|club|event|profile|notice]
 *        [--lang ko] [--webfont none|pretendard]
 *
 * --content JSON 스키마:
 *   { "sections": [ { "heading": "...", "body": "..." }, ... ],
 *     "cta": { "label": "...", "href": "..." } }
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";

// ---------- 인자 파싱 ----------
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        args[key] = "true";
      } else {
        args[key] = next;
        i++;
      }
    }
  }
  return args;
}

function fail(msg) {
  console.error(`[generate] 오류: ${msg}`);
  process.exit(1);
}

// ---------- HTML 이스케이프 ----------
const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ESC[c]);
}
function escapeAttr(s) {
  return escapeHtml(s);
}

// ---------- 톤 프리셋 (3색 이내) ----------
const TONES = {
  minimal: { bg: "#fbfbfd", text: "#1d1d22", accent: "#3b5bdb", dark: false },
  warm: { bg: "#fdfaf6", text: "#2a2420", accent: "#c2410c", dark: false },
  bold: { bg: "#0f1115", text: "#f2f3f5", accent: "#22d3ee", dark: true },
};

// ---------- 종류별 기본 섹션 (콘텐츠 미제공 시) ----------
const KIND_DEFAULTS = {
  landing: [
    { heading: "무엇인가요", body: "[여기에 제품/서비스 한 줄 설명을 넣으세요.]" },
    { heading: "왜 좋은가요", body: "[여기에 핵심 가치 1~2가지를 적으세요.]" },
    { heading: "시작하기", body: "[여기에 다음 행동을 안내하세요.]" },
  ],
  club: [
    { heading: "우리는", body: "[여기에 동아리 소개를 적으세요.]" },
    { heading: "활동", body: "[여기에 정기 활동을 적으세요.]" },
    { heading: "함께해요", body: "[여기에 모임 시간과 참여 방법을 적으세요.]" },
  ],
  event: [
    { heading: "행사 안내", body: "[여기에 행사 개요를 적으세요.]" },
    { heading: "일시·장소", body: "[여기에 날짜·시간·장소를 적으세요.]" },
    { heading: "참가 방법", body: "[여기에 신청 방법을 적으세요.]" },
  ],
  profile: [
    { heading: "소개", body: "[여기에 자기 소개를 적으세요.]" },
    { heading: "하는 일", body: "[여기에 활동/경력을 적으세요.]" },
    { heading: "연락", body: "[여기에 연락 방법을 적으세요.]" },
  ],
  notice: [
    { heading: "공지", body: "[여기에 공지 본문을 적으세요.]" },
    { heading: "상세", body: "[여기에 세부 내용을 적으세요.]" },
  ],
};

// ---------- content 로드 ----------
function loadContent(path, kind) {
  if (!path) {
    return { sections: KIND_DEFAULTS[kind] || KIND_DEFAULTS.landing, cta: null };
  }
  let raw;
  try {
    raw = readFileSync(resolve(path), "utf8");
  } catch (e) {
    fail(`--content 파일을 읽을 수 없습니다: ${path} (${e.message})`);
  }
  let json;
  try {
    json = JSON.parse(raw);
  } catch (e) {
    fail(`--content JSON 파싱 실패: ${e.message}`);
  }
  const sections = Array.isArray(json.sections) ? json.sections : [];
  if (sections.length === 0) {
    fail("--content 의 sections 배열이 비어 있습니다.");
  }
  for (const s of sections) {
    if (typeof s.heading !== "string" || typeof s.body !== "string") {
      fail("각 section 은 문자열 heading 과 body 가 필요합니다.");
    }
  }
  const cta =
    json.cta && typeof json.cta.label === "string"
      ? { label: json.cta.label, href: typeof json.cta.href === "string" ? json.cta.href : "#" }
      : null;
  return { sections, cta };
}

// ---------- 본문 HTML 조립 ----------
function buildSections(sections) {
  return sections
    .map(
      (s) =>
        `      <section class="card">\n` +
        `        <h2>${escapeHtml(s.heading)}</h2>\n` +
        `        <p>${escapeHtml(s.body)}</p>\n` +
        `      </section>`
    )
    .join("\n");
}

function buildCta(cta) {
  if (!cta) return "";
  return (
    `      <p class="cta-wrap">\n` +
    `        <a class="cta" href="${escapeAttr(cta.href)}">${escapeHtml(cta.label)}</a>\n` +
    `      </p>`
  );
}

// ---------- 큰 글씨 토글 (인라인 JS, 최소한) ----------
const LARGE_TEXT_SCRIPT = `    <script>
      (function () {
        var btn = document.getElementById("lt-toggle");
        if (!btn) return;
        function apply(on) {
          document.documentElement.classList.toggle("large", on);
          btn.setAttribute("aria-pressed", on ? "true" : "false");
        }
        btn.addEventListener("click", function () {
          apply(!document.documentElement.classList.contains("large"));
        });
      })();
    </script>`;

// ---------- 전체 문서 ----------
function buildHtml(opts) {
  const { title, tagline, lang, tone, largeText, sectionsHtml, ctaHtml, webfont } = opts;
  const t = TONES[tone] || TONES.minimal;
  const baseSize = largeText ? "21px" : "18px";
  const largeSize = "24px";

  const fontStack = `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif`;
  const webfontLink =
    webfont === "pretendard"
      ? `\n    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">`
      : "";
  const bodyFont =
    webfont === "pretendard" ? `Pretendard, ${fontStack}` : fontStack;

  const taglineHtml = tagline
    ? `        <p class="tagline">${escapeHtml(tagline)}</p>\n`
    : "";

  const ltButton = largeText !== null
    ? `        <button id="lt-toggle" type="button" aria-pressed="${largeText ? "true" : "false"}">큰 글씨</button>\n`
    : "";

  const initialLargeClass = largeText === true ? ' class="large"' : "";

  return `<!doctype html>
<html lang="${escapeAttr(lang)}"${initialLargeClass}>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)}</title>
    <meta name="description" content="${escapeAttr(tagline || title)}">${webfontLink}
    <style>
      :root {
        --bg: ${t.bg};
        --text: ${t.text};
        --accent: ${t.accent};
        --base-size: ${baseSize};
        --large-size: ${largeSize};
      }
      * { box-sizing: border-box; }
      html { font-size: var(--base-size); }
      html.large { font-size: var(--large-size); }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: ${bodyFont};
        line-height: 1.6;
        -webkit-text-size-adjust: 100%;
      }
      .wrap { max-width: 720px; margin: 0 auto; padding: clamp(24px, 5vw, 64px) 20px; }
      header { margin-bottom: 32px; }
      h1 { font-size: 2rem; line-height: 1.2; margin: 0 0 8px; }
      h2 { font-size: 1.25rem; margin: 0 0 8px; color: var(--accent); }
      .tagline { font-size: 1.05rem; opacity: 0.85; margin: 0; }
      .card {
        border: 1px solid color-mix(in srgb, var(--text) 14%, transparent);
        border-radius: 12px;
        padding: 20px 22px;
        margin: 0 0 16px;
      }
      .card p { margin: 0; }
      .cta-wrap { margin-top: 24px; }
      .cta {
        display: inline-block;
        background: var(--accent);
        color: ${t.dark ? "#0f1115" : "#ffffff"};
        text-decoration: none;
        padding: 14px 22px;
        border-radius: 10px;
        font-weight: 600;
      }
      .cta:hover { filter: brightness(1.06); }
      #lt-toggle {
        font: inherit;
        font-size: 0.95rem;
        background: transparent;
        color: var(--accent);
        border: 1px solid var(--accent);
        border-radius: 8px;
        padding: 8px 14px;
        cursor: pointer;
        margin-top: 16px;
      }
      a, button, .cta { outline-offset: 3px; }
      :focus-visible { outline: 3px solid var(--accent); }
      footer { margin-top: 40px; font-size: 0.9rem; opacity: 0.7; }
      @media (max-width: 480px) {
        h1 { font-size: 1.6rem; }
      }
    </style>
  </head>
  <body>
    <main class="wrap">
      <header>
        <h1>${escapeHtml(title)}</h1>
${taglineHtml}${ltButton}      </header>
${sectionsHtml}
${ctaHtml ? ctaHtml + "\n" : ""}      <footer>
        <p>한 파일로 만든 정적 페이지.</p>
      </footer>
    </main>
${largeText !== null ? LARGE_TEXT_SCRIPT + "\n" : ""}  </body>
</html>
`;
}

// ---------- main ----------
function main() {
  const args = parseArgs(process.argv.slice(2));

  const out = args.out;
  const title = args.title;
  if (!out) fail("--out <경로> 가 필요합니다.");
  if (!title) fail("--title <제목> 이 필요합니다.");

  const tone = args.tone || "minimal";
  if (!TONES[tone]) fail(`--tone 은 minimal|warm|bold 중 하나여야 합니다 (받은 값: ${tone}).`);

  const webfont = args.webfont || "none";
  if (webfont !== "none" && webfont !== "pretendard") {
    fail("--webfont 은 none|pretendard 중 하나여야 합니다.");
  }

  // largeText: true|false 면 토글 버튼 노출(기본값 결정). 명시 안 하면 토글 노출(false 시작).
  let largeText = false;
  if (args.largeText === "true") largeText = true;
  else if (args.largeText === "false") largeText = false;
  else if (args.largeText === "off") largeText = null; // 토글 자체 숨김

  const lang = args.lang || "ko";
  const kind = args.kind || "landing";
  const tagline = args.tagline || "";

  const { sections, cta } = loadContent(args.content, kind);

  const html = buildHtml({
    title,
    tagline,
    lang,
    tone,
    largeText,
    webfont,
    sectionsHtml: buildSections(sections),
    ctaHtml: buildCta(cta),
  });

  const outPath = resolve(out);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, html, "utf8");

  console.log(`[generate] 작성 완료: ${outPath}`);
  console.log(`[generate] tone=${tone} largeText=${largeText} webfont=${webfont} sections=${sections.length}`);
  const placeholders = (html.match(/\[여기에/g) || []).length;
  if (placeholders > 0) {
    console.log(`[generate] 경고: placeholder ${placeholders}개가 남아 있습니다. 실제 내용으로 교체하세요.`);
  }
}

main();
