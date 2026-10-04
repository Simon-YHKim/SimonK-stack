#!/usr/bin/env node
// build_album.mjs — photo-album 전용 사진 배치기.
//
// 사진을 "생성"하지 않는다. 사용자가 가진 실사 사진 경로를 받아
// 그리드 / 콜라주 / 페이지 레이아웃으로 배치한 인쇄용 HTML 한 벌을 만든다.
// 전부 결정론적 기하 계산 — 외부 API·키·추가 패키지 없이 Node 표준 라이브러리만 쓴다.
//
// 사용:
//   node build_album.mjs --spec ./album.spec.json --out ./album/index.html
//   node build_album.mjs --photos "a.jpg,b.jpg,c.jpg" --layout grid --title "여행" --out ./album/index.html
//
// 산출 HTML 특징:
//   - A4 @page + page-break-after 로 페이지 경계 보존 (office-docs weasyprint PDF 화 시 그대로 유지)
//   - 사진은 상대경로로 참조 (HTML 위치 기준 재계산)
//   - 큰글씨 기본 (캡션 ≥18px, 제목 ≥24px) — --big false 로 해제
//   - gradient·이모지·둥근 컬러보더 없음, 흰/아이보리 배경 + 사진 + 캡션만

import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve, relative, extname, basename } from "node:path";
import process from "node:process";

const LAYOUTS = new Set(["grid", "collage", "page"]);
const IMAGE_EXT = new Set([".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff"]);

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

function fail(msg) {
  console.error(`[build_album] ${msg}`);
  process.exit(1);
}

function splitList(value) {
  if (typeof value !== "string") return [];
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function isImagePath(p) {
  return IMAGE_EXT.has(extname(p).toLowerCase());
}

// HTML escape — 캡션·제목에 사용자 입력이 들어가므로 항상 이스케이프.
function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// 사진 절대경로 → HTML 출력 위치 기준 상대경로(브라우저·weasyprint 모두 동작).
function toRelSrc(photoPath, outDir) {
  const abs = resolve(photoPath);
  const rel = relative(outDir, abs).split("\\").join("/");
  return rel;
}

// 결정론적 컬럼 수: 사진 수에 따라 2~4열. 1~2장은 사진당 한 칸이 커지도록 최소화.
function autoColumns(count) {
  if (count <= 1) return 1;
  if (count <= 2) return 2;
  if (count <= 6) return 3;
  return 4;
}

// 콜라주 셀 크기 패턴 — 결정론적 시퀀스. 첫 장을 크게(2x2), 이후 1x1·가로2x1 반복.
// 각 항목은 [colSpan, rowSpan].
function collageSpans(count) {
  const spans = [];
  for (let i = 0; i < count; i++) {
    if (i === 0) spans.push([2, 2]); // 표지격 큰 사진
    else if (i % 5 === 2) spans.push([2, 1]); // 주기적 가로 와이드
    else if (i % 7 === 4) spans.push([1, 2]); // 주기적 세로 톨
    else spans.push([1, 1]);
  }
  return spans;
}

// 한 페이지 분량으로 사진을 나눈다(레이아웃별 페이지당 최대 장수).
function paginate(photos, layout, perPage) {
  const max =
    perPage && Number.isFinite(Number(perPage))
      ? Math.max(1, Number(perPage))
      : layout === "page"
        ? 1
        : layout === "collage"
          ? 9
          : 6; // grid 기본 6
  const pages = [];
  for (let i = 0; i < photos.length; i += max) {
    pages.push(photos.slice(i, i + max));
  }
  return pages.length ? pages : [[]];
}

// 캡션은 페이지-로컬 인덱스로 매핑한다. spec 의 각 page.captions 와
// --photos 페이지네이터가 만든 captions 는 모두 그 페이지 photos 와 1:1(같은 순서)이다.
function captionFor(captions, localIndex) {
  if (Array.isArray(captions) && captions.length) {
    const c = captions[localIndex];
    if (typeof c === "string" && c.trim()) return c.trim();
  }
  return ""; // 캡션 강제하지 않음 — 없으면 비움
}

function renderPhoto(photo, caption, outDir) {
  const src = toRelSrc(photo, outDir);
  const alt = esc(basename(photo));
  const cap = caption ? `<figcaption>${esc(caption)}</figcaption>` : "";
  return `<figure class="cell"><img src="${esc(src)}" alt="${alt}" loading="lazy">${cap}</figure>`;
}

function renderGridPage(photos, captions, outDir, columns) {
  const cols = columns && Number(columns) > 0 ? Number(columns) : autoColumns(photos.length);
  const cells = photos
    .map((p, i) => renderPhoto(p, captionFor(captions, i), outDir))
    .join("\n");
  return `<section class="page layout-grid" style="--cols:${cols}">\n${cells}\n</section>`;
}

function renderCollagePage(photos, captions, outDir) {
  const spans = collageSpans(photos.length);
  const cells = photos
    .map((p, i) => {
      const [c, r] = spans[i];
      const fig = renderPhoto(p, captionFor(captions, i), outDir);
      return fig.replace('class="cell"', `class="cell" style="grid-column:span ${c};grid-row:span ${r}"`);
    })
    .join("\n");
  return `<section class="page layout-collage">\n${cells}\n</section>`;
}

function renderBigPage(photos, captions, outDir) {
  // page 레이아웃: 페이지당 사진 1~2장이 주인공. 큰 사진 + 큰 캡션.
  const cells = photos
    .map((p, i) => renderPhoto(p, captionFor(captions, i), outDir))
    .join("\n");
  const span = photos.length >= 2 ? "two" : "one";
  return `<section class="page layout-page span-${span}">\n${cells}\n</section>`;
}

function renderPage(layout, photos, captions, outDir, columns) {
  if (layout === "collage") return renderCollagePage(photos, captions, outDir);
  if (layout === "page") return renderBigPage(photos, captions, outDir);
  return renderGridPage(photos, captions, outDir, columns);
}

function buildCss(big) {
  const capSize = big ? 18 : 14;
  const titleSize = big ? 28 : 20;
  return `
@page { size: A4; margin: 14mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: #fbfaf7; /* 아이보리 — pure white 대신 tinted neutral */
  color: #2b2b30;
  font-family: "Pretendard", "Pretendard Variable", -apple-system, "Apple SD Gothic Neo",
    "Noto Sans KR", "Malgun Gothic", system-ui, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.album-title {
  font-size: ${titleSize + 8}px;
  font-weight: 700;
  text-align: center;
  padding: 24px 16px 8px;
}
.page {
  page-break-after: always;
  break-after: page;
  padding: 8mm 0;
  display: grid;
  gap: 8mm;
}
.page:last-child { page-break-after: auto; break-after: auto; }
.page-title {
  font-size: ${titleSize}px;
  font-weight: 600;
  margin: 0 0 4mm;
}
.cell { margin: 0; display: flex; flex-direction: column; gap: 4px; }
.cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #efeee9;
}
figcaption {
  font-size: ${capSize}px;
  line-height: 1.4;
  text-align: center;
  padding-top: 4px;
}
/* grid: 같은 크기 격자 */
.layout-grid { grid-template-columns: repeat(var(--cols, 3), 1fr); }
.layout-grid .cell img { aspect-ratio: 1 / 1; }
/* collage: 크기 섞인 모자이크 */
.layout-collage {
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 48mm;
  grid-auto-flow: dense;
}
.layout-collage .cell img { height: 100%; }
/* page: 큰 사진 1~2장 */
.layout-page.span-one { grid-template-columns: 1fr; }
.layout-page.span-two { grid-template-columns: 1fr; }
.layout-page .cell img { aspect-ratio: 4 / 3; }
.layout-page figcaption { font-size: ${capSize + 2}px; }
`;
}

function buildHtml(spec, outDir, big) {
  const title = spec.title ? `<h1 class="album-title">${esc(spec.title)}</h1>` : "";
  const pagesHtml = spec.pages
    .map((page) => {
      const layout = LAYOUTS.has(page.layout) ? page.layout : "grid";
      const photos = (page.photos || []).filter(isImagePath);
      if (!photos.length) return "";
      // captions 는 페이지-로컬(이 페이지 photos 와 1:1) 로만 다룬다.
      const pageTitle = page.title ? `<h2 class="page-title">${esc(page.title)}</h2>` : "";
      const body = renderPage(layout, photos, page.captions, outDir, page.columns);
      // 페이지 제목이 있으면 section 내부 첫 요소로 끼워 넣는다.
      return pageTitle ? body.replace(">", `>\n${pageTitle}`) : body;
    })
    .filter(Boolean)
    .join("\n");

  return `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(spec.title || "Photo Album")}</title>
<style>${buildCss(big)}</style>
</head>
<body>
${title}
${pagesHtml}
</body>
</html>
`;
}

function loadSpec(args) {
  // --spec 우선. 없으면 --photos 로 단일 spec 구성.
  if (typeof args.spec === "string") {
    let raw;
    try {
      raw = readFileSync(resolve(args.spec), "utf8");
    } catch (err) {
      fail(`spec 파일을 읽을 수 없습니다: ${args.spec} (${err?.message || err})`);
    }
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      fail(`spec JSON 파싱 실패: ${err?.message || err}`);
    }
    if (!parsed || !Array.isArray(parsed.pages)) {
      fail('spec 에 "pages" 배열이 필요합니다. templates/album.spec.example.json 참고.');
    }
    return parsed;
  }

  const photos = splitList(args.photos);
  if (!photos.length) {
    fail('--spec 또는 --photos 가 필요합니다. 예: --photos "a.jpg,b.jpg,c.jpg" --layout grid');
  }
  const layout = LAYOUTS.has(args.layout) ? args.layout : "grid";
  const captions = splitList(args.caption);
  // --caption 은 전체 사진 순서와 1:1. 페이지 분할 시 누적 오프셋으로 페이지-로컬 슬라이스를 만든다
  // (마지막 페이지가 짧을 수 있으므로 pageNo*size 가정 금지 — running offset 사용).
  let capOffset = 0;
  const pages = paginate(photos, layout, args.perPage).map((chunk) => {
    const slice = captions.length
      ? captions.slice(capOffset, capOffset + chunk.length)
      : undefined;
    capOffset += chunk.length;
    return { layout, photos: chunk, columns: args.columns, captions: slice };
  });
  return { title: typeof args.title === "string" ? args.title : undefined, pages };
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  // --big 기본 on. "--big false" 로만 해제.
  const big = !(args.big === "false");

  const out = typeof args.out === "string" ? resolve(args.out) : resolve("./album/index.html");
  const outDir = dirname(out);

  const spec = loadSpec(args);

  // 사진 경로 유효성 — 이미지 확장자만 통과(파일 내용은 읽지 않는다).
  const allPhotos = spec.pages.flatMap((p) => p.photos || []);
  if (!allPhotos.length) {
    fail("사진 경로가 하나도 없습니다.");
  }
  const nonImage = allPhotos.filter((p) => !isImagePath(p));
  if (nonImage.length) {
    console.error(
      `[build_album] 이미지가 아닌 항목 ${nonImage.length}개는 건너뜁니다: ${nonImage.slice(0, 3).join(", ")}${nonImage.length > 3 ? " ..." : ""}`,
    );
  }

  const html = buildHtml(spec, outDir, big);

  mkdirSync(outDir, { recursive: true });
  writeFileSync(out, html, "utf8");
  console.error(
    `[build_album] pages=${spec.pages.length} photos=${allPhotos.filter(isImagePath).length} big=${big}`,
  );
  console.log(out);
}

main();
