import { spawn } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const chromePath = process.env.CHROME_BIN || (process.platform === 'win32'
  ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : '/usr/bin/google-chrome');
const htmlPath = process.argv[2];
const outputPrefix = process.argv[3];
if (!htmlPath || !outputPrefix) throw new Error('Usage: node interactive-smoke.mjs <template.html> <output-prefix>');

const sample = {
  TASK_TITLE: '격리 후보 브라우저 검증', WRITTEN_KST: '2026-09-29 01:50',
  UPDATED_KST: '', SESSION: 'Codex 로컬 검증', GRADE: 'S',
  REPO_NAME: 'SimonK-stack', BRANCH: 'feat/skill-context-budget-260925', DURATION: '15분',
  WHAT: '구독 범위 내에서 v22 후보를 검증했다.',
  WHY: '설치 전 기능과 안전 경계를 확인하기 위해서다.',
  STATUS: '테스트는 통과했고 설치는 보류 중이다.',
  EXEC_SUMMARY_BULLETS: ['모델·Bot 호출 없음', '설치 준비 플래그는 false'],
  HAS_TERMS: true, TERMS: [{ term: '후보', meaning: '사용자 설치 전의 격리된 패키지' }],
  HAS_DECISIONS: true, DECISIONS: [{ phase: '검증', decision: '설치 보류', reasoning: '남은 게이트 미충족' }],
  HAS_PHASES: true, PHASES: [{ n: '1', duration: '5분', name: '패키지 확인', body: '영수증을 대조했다.' }],
  HAS_DIFF: true, DIFF_GROUPS: [{ area: '문서', files: '2', added: '41', removed: '2' }],
  COMMITS: 'da26231 docs: record v22 isolated candidate verification',
  HAS_VERIFICATION: true,
  VERIFICATIONS: [{ check: 'browser', status_class: 'ok', status: '통과', details: '실제 브라우저 상호작용' }],
  HAS_PERSPECTIVES: false, PERSPECTIVES: [],
  HAS_NEXTUP: true, NEXTUP: [{ label: '구조 결정', desc: 'Codex 오버레이 기본 catalog 영수증 일치' }],
  RAW_COMMIT_LOG: 'da26231 docs: record v22 isolated candidate verification',
  RAW_FILE_LIST: 'README.md\ndocs/INSTALL.md',
};
const escapeHtml = value => String(value).replace(/[&<>"']/g, ch => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[ch]);
function renderBlock(input, context) {
  const section = /{{#([A-Za-z_]+)}}([\s\S]*?){{\/\1}}/g;
  let output = input;
  while (section.test(output)) {
    section.lastIndex = 0;
    output = output.replace(section, (_, name, body) => {
      const value = context[name];
      if (Array.isArray(value)) return value.map(item => renderBlock(body,
        item && typeof item === 'object' ? { ...context, ...item } : { ...context, '.': item })).join('');
      return value ? renderBlock(body, context) : '';
    });
  }
  return output.replace(/{{([^{}]+)}}/g, (_, name) => escapeHtml(context[name] ?? ''));
}
const fixturePath = `${outputPrefix}-fixture.html`;
const source = readFileSync(htmlPath, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
const rendered = renderBlock(source, sample);
if (rendered.includes('{{')) throw new Error('Unrendered template marker remains');
writeFileSync(fixturePath, rendered);

const profile = `${outputPrefix}-profile`;
const chrome = spawn(chromePath, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--disable-sync', '--disable-extensions',
  '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, 'about:blank',
], { windowsHide: true, stdio: 'ignore' });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
try {
  const marker = join(profile, 'DevToolsActivePort');
  for (let i = 0; i < 100 && !existsSync(marker); i++) {
    if (chrome.exitCode !== null) throw new Error(`Chrome exited: ${chrome.exitCode}`);
    await sleep(100);
  }
  if (!existsSync(marker)) throw new Error('Chrome CDP port missing');
  const port = Number(readFileSync(marker, 'utf8').split('\n')[0]);
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = targets.find(target => target.type === 'page');
  if (!page) throw new Error('Chrome page target missing');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let nextId = 0;
  const pending = new Map();
  const exceptions = [];
  const requests = [];
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.exceptionThrown') {
      exceptions.push(message.params?.exceptionDetails?.text || 'runtime exception');
      return;
    }
    if (message.method === 'Network.requestWillBeSent') {
      requests.push(message.params?.request?.url || '');
      return;
    }
    if (!message.id || !pending.has(message.id)) return;
    const { resolve, reject, timer } = pending.get(message.id);
    clearTimeout(timer);
    pending.delete(message.id);
    if (message.error) reject(new Error(`${message.error.code}: ${message.error.message}`));
    else resolve(message.result || {});
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`${method} timed out`)); }, 10000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  };
  const screenshot = async suffix => {
    const result = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    writeFileSync(`${outputPrefix}-${suffix}.png`, Buffer.from(result.data, 'base64'));
  };
  let checkCount = 0;
  const check = (name, value) => {
    if (!value) throw new Error(`FAIL ${name}`);
    checkCount++;
    console.log(`PASS ${name}`);
  };

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 375, height: 900, deviceScaleFactor: 1, mobile: true });
  await send('Page.navigate', { url: pathToFileURL(fixturePath).href });
  for (let i = 0; i < 50; i++) {
    if (await evaluate('document.readyState === "complete" && document.documentElement.classList.contains("js")')) break;
    await sleep(100);
  }
  check('script startup', await evaluate('document.documentElement.classList.contains("js")'));
  check('populated fixture', await evaluate('document.querySelector("h1").textContent === "격리 후보 브라우저 검증" && !document.body.textContent.includes("{{")'));
  check('initial summary tab', await evaluate('!document.querySelector("#panel-summary").hidden && document.querySelector("#panel-detail").hidden && document.querySelector("#tab-summary").getAttribute("aria-selected") === "true"'));
  await screenshot('mobile-summary');
  check('mobile has no horizontal overflow', await evaluate('document.documentElement.scrollWidth <= window.innerWidth'));

  await evaluate('document.querySelector("#tab-detail").click()');
  check('detail tab click', await evaluate('document.querySelector("#panel-summary").hidden && !document.querySelector("#panel-detail").hidden && document.querySelector("#tab-detail").getAttribute("aria-selected") === "true"'));
  await screenshot('mobile-detail');
  await evaluate('document.querySelector("#tab-detail").dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowLeft", bubbles:true}))');
  check('tab keyboard navigation', await evaluate('!document.querySelector("#panel-summary").hidden && document.activeElement.id === "tab-summary"'));

  await evaluate(`(() => {
    const node = document.querySelector('[data-memo="요약 · 무엇을"] p').firstChild;
    const range = document.createRange(); range.selectNodeContents(node);
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    document.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
  })()`);
  await sleep(100);
  check('selection memo affordance', await evaluate('!document.querySelector("#memo-float").hidden'));
  await evaluate('document.querySelector("#memo-float").click()');
  check('memo capture and panel', await evaluate('document.querySelector("#memo-count").textContent === "1" && !document.querySelector("#memo-panel").hidden && document.querySelector("#memo-list blockquote").textContent.includes("v22")'));
  await screenshot('mobile-memo');
  await evaluate(`(() => { const t=document.querySelector('#memo-list textarea'); t.value='설치 게이트 유지'; t.dispatchEvent(new Event('input',{bubbles:true})); })()`);
  check('memo local persistence', await evaluate('document.querySelector("#memo-store").textContent.includes("브라우저") && Object.keys(localStorage).some(k => k.startsWith("simonk-memo:"))'));
  await evaluate('document.querySelector("#memo-close").click()');
  check('memo close restores focus', await evaluate('document.querySelector("#memo-panel").hidden && document.activeElement.id === "memo-toggle"'));

  await send('Page.reload', { ignoreCache: true });
  for (let i = 0; i < 50; i++) {
    if (await evaluate('document.readyState === "complete" && document.documentElement.classList.contains("js")')) break;
    await sleep(100);
  }
  check('memo survives reload', await evaluate('document.querySelector("#memo-count").textContent === "1" && document.querySelector("#memo-list textarea").value === "설치 게이트 유지"'));
  await evaluate('document.querySelector("#memo-toggle").click()');
  await evaluate(`(() => {
    Object.defineProperty(navigator, 'clipboard', {value:{writeText:()=>Promise.reject(new Error('denied'))}, configurable:true});
    document.execCommand=()=>false;
    document.querySelector('#memo-copy').click();
  })()`);
  await sleep(100);
  check('copy fallback exposes prompt', await evaluate('!document.querySelector("#memo-out").hidden && document.querySelector("#memo-out").value.includes("설치 게이트 유지") && document.querySelector("#memo-status").textContent.includes("직접 복사")'));

  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
  check('dark palette applied', await evaluate('getComputedStyle(document.body).backgroundColor === "rgb(15, 14, 26)"'));
  check('desktop has no horizontal overflow', await evaluate('document.documentElement.scrollWidth <= window.innerWidth'));
  await screenshot('desktop-dark');

  await evaluate('window.dispatchEvent(new Event("beforeprint"))');
  await send('Emulation.setEmulatedMedia', { media: 'print' });
  check('print expands detail', await evaluate('[...document.querySelectorAll("details")].every(d=>d.open) && getComputedStyle(document.querySelector(".banner")).display === "none" && getComputedStyle(document.querySelector("#panel-detail")).display === "block"'));
  const pdf = await send('Page.printToPDF', { printBackground: true });
  check('browser PDF generated', Buffer.from(pdf.data, 'base64').subarray(0, 5).toString() === '%PDF-');
  check('no external requests', requests.every(url => url.startsWith('file:') || url.startsWith('about:') || url.startsWith('data:')));
  check('no JavaScript exceptions', exceptions.length === 0);
  writeFileSync(`${outputPrefix}-result.json`, JSON.stringify({ status: 'passed', checks: checkCount, exceptions, request_count: requests.length, screenshots: ['mobile-summary', 'mobile-detail', 'mobile-memo', 'desktop-dark'], pdf_bytes: Buffer.from(pdf.data, 'base64').length, fixture: fixturePath }, null, 2));
  await send('Browser.close').catch(() => {});
} finally {
  if (socket?.readyState === WebSocket.OPEN) socket.close();
  if (chrome.exitCode === null) chrome.kill();
}
