#!/usr/bin/env node
/**
 * check.mjs — 생성한 단일 HTML 파일을 자가 점검한다 (결정론, 네트워크 없음).
 *
 * 검사 항목:
 *  1. 단일 파일: 외부 <link rel=stylesheet> / <script src> / @import 없음
 *     (webfont 옵션 사용 시 stylesheet 1개까지 허용)
 *  2. doctype + <html lang> + <meta charset> + <meta viewport>
 *  3. <title> 비어있지 않음, <h1> 정확히 1개
 *  4. 본문 글자 크기 >= 18px (--base-size / html font-size)
 *  5. 반응형: max-width 컨테이너 존재
 *  6. 색상 3개 이내(--bg/--text/--accent), 그라데이션/glassmorphism 없음
 *  7. placeholder "[여기에 ...]" 잔존 시 경고
 *
 * 사용:  node check.mjs <html 파일 경로>
 * 종료코드: 통과 0, 실패 항목 있으면 1 (경고만 있으면 0).
 */

import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

function fail(msg) {
  console.error(`[check] 오류: ${msg}`);
  process.exit(2);
}

const target = process.argv[2];
if (!target) fail("점검할 HTML 파일 경로를 인자로 주세요.");
const abs = resolve(target);
if (!existsSync(abs)) fail(`파일이 없습니다: ${abs}`);

const html = readFileSync(abs, "utf8");
const lower = html.toLowerCase();

const errors = [];
const warnings = [];

// 1. 단일 파일 — 외부 리소스
const extStylesheets = (html.match(/<link[^>]+rel=["']?stylesheet["']?[^>]*>/gi) || []);
const extScripts = (html.match(/<script[^>]+src=/gi) || []);
const cssImports = (html.match(/@import\b/gi) || []);
if (extStylesheets.length > 1) {
  errors.push(`외부 stylesheet 가 ${extStylesheets.length}개입니다 (최대 1개: 웹폰트 옵션).`);
}
if (extScripts.length > 0) {
  errors.push(`외부 <script src> 가 ${extScripts.length}개입니다 (단일 파일 위반).`);
}
if (cssImports.length > 0) {
  errors.push(`@import 가 ${cssImports.length}개입니다 (단일 파일 위반).`);
}

// 2. 문서 골격
if (!/^\s*<!doctype html>/i.test(html)) errors.push("<!doctype html> 가 없습니다.");
if (!/<html[^>]*\blang=/i.test(html)) errors.push("<html lang=...> 속성이 없습니다.");
if (!/<meta[^>]+charset/i.test(html)) errors.push("<meta charset> 가 없습니다.");
if (!/<meta[^>]+name=["']?viewport/i.test(html)) errors.push("<meta name=viewport> 가 없습니다 (반응형).");

// 3. title / h1
const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
if (!titleMatch || titleMatch[1].trim() === "") errors.push("<title> 이 비어 있거나 없습니다.");
const h1Count = (html.match(/<h1[\s>]/gi) || []).length;
if (h1Count !== 1) errors.push(`<h1> 이 ${h1Count}개입니다 (정확히 1개여야 함).`);

// 4. 글자 크기 >= 18px
const sizeMatch = html.match(/--base-size:\s*(\d+(?:\.\d+)?)px/i) || html.match(/html\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px/i);
if (sizeMatch) {
  const px = parseFloat(sizeMatch[1]);
  if (px < 18) errors.push(`기본 글자 크기가 ${px}px 입니다 (접근성: 18px 이상 권장).`);
} else {
  warnings.push("기본 글자 크기(px)를 확인하지 못했습니다.");
}

// 5. 반응형 컨테이너
if (!/max-width\s*:/i.test(html)) errors.push("max-width 컨테이너가 없습니다 (반응형 위반).");

// 6. 색상 수 / 금지 패턴
const colorVars = (html.match(/--(?:bg|text|accent)\s*:/gi) || []).length;
if (colorVars > 3) warnings.push(`핵심 색상 토큰이 ${colorVars}개로 보입니다 (3색 이내 권장).`);
if (/linear-gradient|radial-gradient/i.test(lower)) errors.push("그라데이션이 발견되었습니다 (AI slop 금지 규칙).");
if (/backdrop-filter|filter:\s*blur/i.test(lower)) errors.push("glassmorphism(backdrop-filter/blur)가 발견되었습니다.");

// 7. placeholder 잔존
const placeholders = (html.match(/\[여기에[^\]]*\]/g) || []).length;
if (placeholders > 0) warnings.push(`placeholder "[여기에 ...]" ${placeholders}개가 남아 있습니다. 실제 내용으로 교체하세요.`);

// ---------- 보고 ----------
console.log(`[check] 대상: ${abs}`);
if (errors.length === 0) {
  console.log("[check] PASS — 모든 필수 항목 통과.");
} else {
  console.log(`[check] FAIL — 필수 항목 ${errors.length}개 미통과:`);
  for (const e of errors) console.log(`  - ${e}`);
}
for (const w of warnings) console.log(`[check] 경고: ${w}`);

process.exit(errors.length === 0 ? 0 : 1);
