#!/usr/bin/env node
/**
 * preview.mjs — 생성한 HTML 파일을 기본 브라우저에서 연다 (서버 불필요).
 *
 * OS 감지: win32=`start`, darwin=`open`, 그 외=`xdg-open`.
 * 브라우저를 열지 못하면 file:// URL 을 출력하니 사용자가 직접 붙여 넣으면 된다.
 *
 * 사용:  node preview.mjs <html 파일 절대경로>
 */

import { existsSync, statSync } from "node:fs";
import { resolve, sep } from "node:path";
import { spawn } from "node:child_process";
import { platform } from "node:os";
import { pathToFileURL } from "node:url";

function fail(msg) {
  console.error(`[preview] 오류: ${msg}`);
  process.exit(1);
}

const target = process.argv[2];
if (!target) fail("열 HTML 파일 경로를 인자로 주세요. 예: node preview.mjs ./index.html");

const abs = resolve(target);
if (!existsSync(abs)) fail(`파일이 없습니다: ${abs}`);
if (!statSync(abs).isFile()) fail(`파일이 아닙니다: ${abs}`);

const fileUrl = pathToFileURL(abs).href;
const os = platform();

let cmd, cmdArgs, useShell;
if (os === "win32") {
  // start 는 cmd 내장 명령. 첫 따옴표 인자는 창 제목으로 먹으므로 빈 제목을 먼저 준다.
  cmd = "cmd";
  cmdArgs = ["/c", "start", "", abs];
  useShell = false;
} else if (os === "darwin") {
  cmd = "open";
  cmdArgs = [abs];
  useShell = false;
} else {
  cmd = "xdg-open";
  cmdArgs = [abs];
  useShell = false;
}

const child = spawn(cmd, cmdArgs, { shell: useShell, stdio: "ignore", detached: true });

child.on("error", () => {
  console.log("[preview] 자동으로 브라우저를 열지 못했습니다. 아래 주소를 브라우저에 직접 붙여 넣으세요:");
  console.log(fileUrl);
  process.exit(0);
});

child.on("spawn", () => {
  child.unref();
  console.log(`[preview] 브라우저에서 여는 중: ${abs}`);
  console.log(`[preview] 안 열리면 이 주소를 직접 붙여 넣으세요: ${fileUrl}`);
  process.exit(0);
});
