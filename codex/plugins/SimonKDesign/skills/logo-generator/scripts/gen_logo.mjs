#!/usr/bin/env node
// gen_logo.mjs — 로고/브랜드 마크 컨셉을 Gemini 이미지 생성으로 PNG 저장.
//
// 사용:
//   node gen_logo.mjs --prompt "<프롬프트>" --kind symbol --out out.png [--n 4]
//
// 환경 변수: GEMINI_API_KEY (없으면 GOOGLE_API_KEY).
//
// 로고 종류(--kind):
//   symbol     심볼/아이콘 마크 (텍스트 없는 추상·구상 형태)
//   wordmark   워드마크 (브랜드명 타이포그래피)
//   combination 콤비네이션 (심볼 + 워드마크)
//   monogram   모노그램 (이니셜 레터마크)
//
// 종류별로 정사각(1024x1024) 캔버스에 단색 배경 + 중앙 정렬을 강제해
// 이후 벡터화(SVG)·배경 제거가 쉽도록 한다.

import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

// === 이미지 생성 모델 ID — 최신 이미지 모델로 교체 가능. 이 한 줄만 바꾸면 된다. ===
const MODEL = 'gemini-2.5-flash-image';

// 로고 종류별 프롬프트 보강 문구. 벡터화 친화 + AI-slop 방지를 결정론적으로 주입한다.
const KINDS = {
  symbol:
    '심볼/아이콘 마크. 텍스트·글자 없음. 단일 추상 또는 구상 형태 하나. ' +
    '평평한(flat) 벡터 스타일, 단색 또는 2색 이내, 그라데이션·그림자·3D 효과 없음. ' +
    '명확한 실루엣과 두꺼운 균일 선폭으로 작은 크기에서도 식별 가능.',
  wordmark:
    '워드마크 로고. 브랜드명만 타이포그래피로 표현. 별도 아이콘 없음. ' +
    '글자 자간·정렬 정확, 커스텀 레터폼 허용. 단색, 장식 효과 없음. ' +
    '글자 형태가 또렷하고 가독성 높게.',
  combination:
    '콤비네이션 로고. 위쪽 또는 왼쪽에 심볼, 그 옆/아래에 브랜드명 워드마크. ' +
    '심볼과 텍스트의 시각 무게 균형. 평평한 벡터 스타일, 단색 또는 2색 이내, 효과 없음.',
  monogram:
    '모노그램 레터마크. 브랜드 이니셜 1~3글자를 기하학적으로 결합한 마크. ' +
    '단순·대칭·균형. 평평한 벡터 스타일, 단색 또는 2색 이내, 효과 없음.',
};

// AI-slop 방지: 모든 종류에 공통으로 강제하는 네거티브/사양 문구.
const COMMON_SPEC =
  '[필수 사양] 정사각 1024x1024. 단색 평면 배경(흰색 또는 지정 배경색) 위 중앙 정렬, 충분한 여백. ' +
  '하나의 마크만. 여러 변형을 한 캔버스에 늘어놓지 말 것. 목업·명함·간판 합성 없이 마크 단독. ' +
  '금지: gradient, glassmorphism, 사실적 질감, 3D 베벨, 드롭섀도, 스톡 클립아트 느낌, ' +
  '이모지, 무지개·4색 이상 multi-color, bevel/emboss, 워터마크, 불필요한 장식. ' +
  '지향: 절제된 모노톤(브랜드 색 3색 이내), 평평한 벡터, 굵고 균일한 선, 단순한 형태, 작은 크기에서도 식별 가능한 실루엣.';

function die(msg, code = 1) {
  console.error(`\n[logo-generator] ${msg}\n`);
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
  node gen_logo.mjs --prompt "<프롬프트>" --kind <symbol|wordmark|combination|monogram> --out <경로.png> [--n <개수>]

옵션:
  --prompt   (필수) 브랜드·컨셉 프롬프트 (브랜드명·업종·톤·색 등)
  --kind     로고 종류. 기본 symbol
  --out      저장 경로. 미지정 시 ./logo-<kind>-<timestamp>.png
  --n        같은 프롬프트로 만들 변형 개수. 기본 4 (시안 비교용), 최대 8

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

  const kind = typeof args.kind === 'string' ? args.kind : 'symbol';
  const kindSpec = KINDS[kind];
  if (!kindSpec) {
    die(`--kind 값이 올바르지 않습니다: "${kind}". 허용: ${Object.keys(KINDS).join(', ')}`);
  }

  let n = 4; // 로고는 보통 여러 시안을 비교한다 — 기본값 4.
  if (args.n !== undefined && args.n !== true) {
    const parsed = parseInt(String(args.n), 10);
    if (Number.isNaN(parsed) || parsed < 1) die(`--n 은 1 이상의 정수여야 합니다: "${args.n}"`);
    n = Math.min(parsed, 8); // 유료 API — 안전 상한
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const baseOut =
    typeof args.out === 'string' ? args.out : resolve(process.cwd(), `logo-${kind}-${ts}.png`);

  const apiKey = resolveApiKey();
  const { GoogleGenAI } = await loadSdk();

  let ai;
  try {
    ai = new GoogleGenAI({ apiKey });
  } catch (err) {
    die(`SDK 초기화 실패: ${err?.message || err}`);
  }

  // 사용자 프롬프트 + 종류별 사양 + 공통 사양을 합쳐 벡터화 친화·AI-slop 방지를 강제한다.
  const fullPrompt = `${prompt}\n\n[로고 종류] ${kindSpec}\n\n${COMMON_SPEC}`;

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
    console.log(`[logo-generator] 저장: ${outPath}`);
  }

  console.log(`\n[logo-generator] 완료 — ${saved.length}개 시안 (${kind}, 1024x1024).`);
  for (const p of saved) console.log(`  ${p}`);
  console.log(
    '\n다음 단계: 마음에 드는 시안을 골라 벡터화(SVG)·배경 제거하세요. SKILL.md "벡터화 / export" 섹션 참고.'
  );
}

main().catch((err) => die(`예기치 못한 오류: ${err?.stack || err?.message || err}`));
