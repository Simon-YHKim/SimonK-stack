#!/usr/bin/env node
// gen_lineart.mjs — coloring-art 전용 라인아트/색칠공부 페이지 생성기.
//
// social-graphic 의 gen_graphic.mjs 와 동일한 Gemini 호출 패턴을 따른다:
//   - @google/genai GoogleGenAI 클라이언트 (API key 또는 Vertex)
//   - 모델은 상단 상수 MODEL 로 고정
//   - 환경변수·인자 방어적 처리, 실패 시 명확한 메시지로 종료
//
// 차이점: 라인아트 전용 프롬프트 프리픽스를 강제로 붙여서
//   "굵은 검은 외곽선 only / 음영 없음 / 흰 배경 / A4 인쇄 적합" 을 보장한다.
//
// 사용:
//   node gen_lineart.mjs --subject "공룡 티라노" --age 5 --out ./out/dino.png
//   node gen_lineart.mjs --subject "cute cat in a garden" --age 8 --difficulty medium
//
// 환경변수 (gemini.ts 와 동일 규약):
//   GOOGLE_API_KEY            (직접 호출 시 필수)
//   EXPO_PUBLIC_USE_VERTEX    "true" 면 Vertex 경로
//   GOOGLE_CLOUD_PROJECT      (Vertex 시 필수)
//   GOOGLE_CLOUD_LOCATION     (Vertex, 기본 us-central1)
//   GEMINI_IMAGE_MODEL        (선택, 기본 모델 override)

import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import process from "node:process";

import { GoogleGenAI } from "@google/genai";

// 이미지 생성 모델 상수. gemini.ts 의 MODELS 와 같은 "상단 상수" 패턴.
const MODEL = process.env.GEMINI_IMAGE_MODEL || "gemini-2.5-flash-image";

// 라인아트 전용 프롬프트 프리픽스 — 절대 비우지 않는다.
// 색칠공부 페이지의 핵심 제약(검은 외곽선만, 음영 0, 흰 배경, 인쇄 적합)을 강제.
const LINEART_PREFIX =
  "black outline coloring book page, no shading, no grayscale, no fill, " +
  "pure white background, thick clean black contour lines only, " +
  "high contrast, simple closed shapes easy to color inside, " +
  "centered composition with generous margins, printable on A4, " +
  "child-safe friendly cartoon style. Subject: ";

// 난이도 → 면 단순화 정도. 어릴수록 면을 크게/적게.
const DIFFICULTY = {
  easy: "very few large simple areas, extra-thick outlines, minimal detail",
  medium: "moderate number of areas, clear outlines, some friendly detail",
  hard: "more areas and patterns to color, still clean closed outlines",
};

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        args[key] = true;
      } else {
        args[key] = next;
        i++;
      }
    }
  }
  return args;
}

function fail(msg) {
  console.error(`[gen_lineart] ${msg}`);
  process.exit(1);
}

function ageToDifficulty(age) {
  const n = Number(age);
  if (!Number.isFinite(n)) return "medium";
  if (n <= 4) return "easy";
  if (n <= 7) return "easy";
  if (n <= 10) return "medium";
  return "hard";
}

function getClient() {
  const useVertex = process.env.EXPO_PUBLIC_USE_VERTEX === "true";
  if (useVertex) {
    const project = process.env.GOOGLE_CLOUD_PROJECT;
    if (!project) fail("Vertex 경로인데 GOOGLE_CLOUD_PROJECT 가 없습니다.");
    return new GoogleGenAI({
      vertexai: true,
      project,
      location: process.env.GOOGLE_CLOUD_LOCATION || "us-central1",
    });
  }
  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    fail(
      "GOOGLE_API_KEY 가 없습니다. 직접 호출이면 API key 를, GCP면 EXPO_PUBLIC_USE_VERTEX=true 를 설정하세요.",
    );
  }
  return new GoogleGenAI({ apiKey });
}

function extractImage(response) {
  const parts = response?.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    const data = part?.inlineData?.data;
    if (data) {
      return {
        buffer: Buffer.from(data, "base64"),
        mime: part.inlineData.mimeType || "image/png",
      };
    }
  }
  return null;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const subject = typeof args.subject === "string" ? args.subject.trim() : "";
  if (!subject) {
    fail('--subject 가 필요합니다. 예: --subject "공룡 티라노"');
  }

  const age = args.age;
  const difficulty =
    typeof args.difficulty === "string" && DIFFICULTY[args.difficulty]
      ? args.difficulty
      : ageToDifficulty(age);

  const out = typeof args.out === "string" ? resolve(args.out) : resolve("./lineart.png");

  // 안전·연령 적합 가드: 폭력/공포/성인 소재 단어가 들어오면 거부.
  const banned = /\b(blood|gore|weapon|gun|knife|sexy|nude|kill|horror|scary)\b/i;
  if (banned.test(subject)) {
    fail("아동용 색칠 페이지에 부적합한 소재입니다. 다른 소재로 다시 시도하세요.");
  }

  const prompt =
    LINEART_PREFIX +
    subject +
    `. Line density: ${DIFFICULTY[difficulty]}.` +
    (age ? ` Target age ${age}.` : "") +
    " Do NOT add any text, letters, watermark, color, or gray shading.";

  const ai = getClient();

  console.error(`[gen_lineart] model=${MODEL} difficulty=${difficulty} subject="${subject}"`);

  let response;
  try {
    response = await ai.models.generateContent({
      model: MODEL,
      contents: prompt,
      // 이미지 모델이 이미지를 반드시 반환하도록 명시(누락 시 일부 모델은 텍스트만 반환).
      // SDK 버전이 이 값을 거부하면 config 줄을 제거하세요.
      config: { responseModalities: ["IMAGE", "TEXT"] },
    });
  } catch (err) {
    fail(`Gemini 호출 실패: ${err?.message || err}`);
  }

  const image = extractImage(response);
  if (!image) {
    fail(
      "응답에 이미지가 없습니다. 모델이 이미지 출력을 지원하는지(GEMINI_IMAGE_MODEL), 프롬프트가 차단되지 않았는지 확인하세요.",
    );
  }

  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, image.buffer);
  console.log(out);
}

main().catch((err) => fail(err?.message || String(err)));
