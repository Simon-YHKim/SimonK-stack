#!/usr/bin/env node
// gen_graphic.mjs — SNS/마케팅 그래픽을 Gemini 이미지 생성으로 PNG 저장.
//
// 사용:
//   node gen_graphic.mjs --prompt "<프롬프트>" --aspect 4:5 --out out.png [--n 1]
//
// 환경 변수: GEMINI_API_KEY (없으면 GOOGLE_API_KEY).
//
// 비율 프리셋:
//   1:1  -> 1080x1080 (인스타 정사각)
//   4:5  -> 1080x1350 (인스타 피드 세로, 카드뉴스)
//   9:16 -> 1080x1920 (스토리/릴스)

import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

// === 이미지 생성 모델 ID — 최신 이미지 모델로 교체 가능. 이 한 줄만 바꾸면 된다. ===
const MODEL = 'gemini-2.5-flash-image';

const ASPECTS = {
  '1:1': { w: 1080, h: 1080 },
  '4:5': { w: 1080, h: 1350 },
  '9:16': { w: 1080, h: 1920 },
};

function die(msg, code = 1) {
  console.error(`\n[social-graphic] ${msg}\n`);
  process.exit(code);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) {
      args[key] = true; // flag
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

function usage() {
  console.error(`
사용법:
  node gen_graphic.mjs --prompt "<프롬프트>" --aspect <1:1|4:5|9:16> --out <경로.png> [--n <개수>]

옵션:
  --prompt   (필수) 이미지 생성 프롬프트
  --aspect   비율 프리셋. 기본 1:1
  --out      저장 경로. 미지정 시 ./social-graphic-<timestamp>.png
  --n        같은 프롬프트로 만들 변형 개수. 기본 1

환경 변수:
  GEMINI_API_KEY  (없으면 GOOGLE_API_KEY)
`);
}

function resolveApiKey() {
  const key = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!key) {
    die(
      'API 키가 없습니다.\n' +
        '  PowerShell:  $env:GEMINI_API_KEY = "<your-key>"\n' +
        '  bash:        export GEMINI_API_KEY="<your-key>"\n' +
        '키 발급: https://aistudio.google.com/apikey'
    );
  }
  return key;
}

async function loadSdk() {
  try {
    const mod = await import('@google/genai');
    return mod;
  } catch {
    die(
      '@google/genai 패키지를 찾을 수 없습니다. 설치 후 다시 실행하세요.\n' +
        '  npm i @google/genai\n' +
        '(Node 18+ 필요)'
    );
  }
}

// 응답에서 첫 이미지 part 의 base64 데이터를 안전하게 뽑아낸다.
function extractImageBase64(response) {
  const candidates = response?.candidates;
  if (!Array.isArray(candidates)) return null;
  for (const cand of candidates) {
    const parts = cand?.content?.parts;
    if (!Array.isArray(parts)) continue;
    for (const part of parts) {
      const data = part?.inlineData?.data || part?.inline_data?.data;
      if (typeof data === 'string' && data.length > 0) return data;
    }
  }
  return null;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help || args.h) {
    usage();
    process.exit(0);
  }

  const prompt = typeof args.prompt === 'string' ? args.prompt.trim() : '';
  if (!prompt) {
    usage();
    die('--prompt 가 필요합니다.');
  }

  const aspect = typeof args.aspect === 'string' ? args.aspect : '1:1';
  const preset = ASPECTS[aspect];
  if (!preset) {
    die(`--aspect 값이 올바르지 않습니다: "${aspect}". 허용: ${Object.keys(ASPECTS).join(', ')}`);
  }

  let n = 1;
  if (args.n !== undefined && args.n !== true) {
    const parsed = parseInt(String(args.n), 10);
    if (Number.isNaN(parsed) || parsed < 1) die(`--n 은 1 이상의 정수여야 합니다: "${args.n}"`);
    n = Math.min(parsed, 8); // 유료 API — 안전 상한
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const baseOut =
    typeof args.out === 'string' ? args.out : resolve(process.cwd(), `social-graphic-${ts}.png`);

  const apiKey = resolveApiKey();
  const { GoogleGenAI } = await loadSdk();

  let ai;
  try {
    ai = new GoogleGenAI({ apiKey });
  } catch (err) {
    die(`SDK 초기화 실패: ${err?.message || err}`);
  }

  // 비율·여백 힌트를 프롬프트에 보강(모델이 비율 파라미터를 직접 안 받을 수 있으므로 텍스트로도 명시).
  const fullPrompt =
    `${prompt}\n\n` +
    `[출력 사양] 종횡비 ${aspect} (${preset.w}x${preset.h}px), 세로/가로 비율 정확히 유지. ` +
    `소셜 미디어 안전영역 고려해 핵심 요소는 중앙 영역에 배치. 모노톤 절제된 색, 과잉장식 없음.`;

  const saved = [];
  for (let i = 0; i < n; i++) {
    let response;
    try {
      response = await ai.models.generateContent({
        model: MODEL,
        contents: fullPrompt,
        // 이미지 모델이 이미지를 반드시 반환하도록 명시(누락 시 일부 모델은 텍스트만 반환).
        // SDK 버전이 이 값을 거부하면 config 줄을 제거하세요.
        config: { responseModalities: ['IMAGE', 'TEXT'] },
      });
    } catch (err) {
      die(
        `이미지 생성 API 호출 실패 (${i + 1}/${n}): ${err?.message || err}\n` +
          `모델 ID 가 더 이상 유효하지 않다면 스크립트 상단 MODEL 상수를 최신 이미지 모델로 교체하세요.`
      );
    }

    const b64 = extractImageBase64(response);
    if (!b64) {
      const txt = response?.text || '(텍스트 응답 없음)';
      die(
        `응답에 이미지가 없습니다 (${i + 1}/${n}).\n` +
          `모델이 이미지를 반환하지 않았습니다 (안전 필터 또는 모델 미지원 가능).\n` +
          `모델 응답 텍스트: ${txt}`
      );
    }

    const outPath = n > 1 ? baseOut.replace(/(\.[^.]+)?$/, `-${i + 1}$1`) : baseOut;
    try {
      mkdirSync(dirname(outPath), { recursive: true });
      writeFileSync(outPath, Buffer.from(b64, 'base64'));
    } catch (err) {
      die(`파일 저장 실패 (${outPath}): ${err?.message || err}`);
    }
    saved.push(outPath);
    console.log(`[social-graphic] 저장: ${outPath}`);
  }

  console.log(`\n[social-graphic] 완료 — ${saved.length}장 (${aspect}, ${preset.w}x${preset.h}).`);
  for (const p of saved) console.log(`  ${p}`);
}

main().catch((err) => die(`예기치 못한 오류: ${err?.stack || err?.message || err}`));
