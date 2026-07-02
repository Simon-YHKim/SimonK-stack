---
owner: claude
note: "append-only 인시던트 원장. 와치독(§5/§13)·복구 작업이 한 줄씩 추가. 정본 복구절차=RUNBOOK.md, 정본 규칙=PROTOCOL.md."
last-sync: 2026-06-14
---

# INCIDENTS.md — 허브 인시던트 원장 (append-only)

> 무인 운용 중 발생한 장애·복구를 시간순으로 한 줄씩 남긴다. 형식:
> `[YYYY-MM-DD / HH:MM:SS KST] | 신호 | 원인 | 복구 | 재발방지`
> 반복 3회+ 패턴은 SimonKWiki 교훈(§18)으로 승격하고 여기에 링크.

## 로그
- [2026-06-14 / 13:30:00 KST] | SETUP | RUNBOOK/INCIDENTS 신설(허브 개선 패스) | n/a — 와치독·복구 표면 신설. monitor/hub-health는 신호 생산만 했고 'responder'가 없었음(BACKLOG #5) | RUNBOOK 룩업표 + 와치독 듀티(ROUTING Grok)로 신호→대응 연결
- [2026-06-15 / 08:21:00 KST] | 데몬 중복(각 AI 2개=6, 03:22+03:23 이중런치) | HUB-STARTUP 모드A/런처에 중복 spawn 가드 없음 → cycle 중복·git race | 디렉터가 즉시 후발 PID kill(각 1개=3) | hub-daemon.ps1에 lane(-Only)별 named-mutex 단일인스턴스 가드(중복이면 exit 0). RUNBOOK §데몬중복
- [2026-06-15 / 08:21:00 KST] | codex STATUS.md 118KB 비대(§28 size-guard 통과) | commit.ps1 size-guard가 모든 .md 일괄 256KB → STATUS도 미만이면 통과 | codex 단일라이터가 STATUS 절단+gitignored *.log 회전(directed task 발행) | commit.ps1에 STATUS.md 전용 64KB 캡(초과 시 SIZE FAIL). RUNBOOK §STATUS비대
- [2026-06-15 / 08:21:00 KST] | .watchdog-state.json UTF-8 BOM(hub-health FAIL) | hub-watchdog.ps1 Set-Content -Encoding utf8 → PS5.1에서 BOM 추가 | 기존 BOM .NET ReadAllText→WriteAllText(no-BOM) 제거 | hub-watchdog write를 [IO.File]::WriteAllText+UTF8Encoding($false)로 교정. FAIL=0 확인
- [2026-06-15 / 08:21:00 KST] | outbox frontmatter 225/1761 malformed(WARN) | 초기 메시지가 frontmatter 키 contract 전 작성 | 점진 정리(신규는 contract 준수) | 필수키 contract를 PROTOCOL/RULES에 명확화(후속). 비차단 WARN 유지
- [2026-06-15 / 08:26:00 KST] | claude(실행자) STATUS.md stale(06-14) | /loop 사이클 STATUS 1줄 갱신 step 누락 | 실행자 STATUS 현행화(O-13/14/15) | §12 루프 step "매 사이클 STATUS 1줄" — 이 갱신으로 이행
- [2026-07-03 / 01:37:29 KST] | codex 브랜치 HEAD 하이재킹 — 206커밋이 master 밖 유령 브랜치에 적재, 오프머신 백업 21h 공백 | 데몬 codex spawn(danger-full-access)이 공유 허브 트리에 checkout -b, 브랜치 가드 전무 | master ff-머지 + stray 삭제 | commit.ps1 BRANCH GUARD(non-master 거부) + 데몬 BRANCH-HEAL(사이클말 자동 ff복귀) + watchdog hub-head-off-master 알림 + PROTOCOL §5 "master 단일 브랜치" 명문화
- [2026-07-03 / 01:37:29 KST] | HubBackup 06-20부터 매일 non-ff 거부 무음 실패(백업 공백 13일) | origin에 이관기 스냅샷 커밋(6e52329e)만 존재해 로컬과 분기 — 아무도 backup log를 안 읽음 | `-s ours` 병합(내용=13일 더 새로운 로컬 유지, 히스토리 결합) 후 push 재개(34c5155f) | 백업은 "성공 로그"가 아니라 push 결과를 검증해야 — hub-backup synced= 필드 확인 습관 + RUNBOOK
- [2026-07-03 / 01:37:29 KST] | 원격 오더 채널 12일 무소비(마지막 DONE 06-21) — Simon 오더가 픽업 없이 방치 | 소비자=인터랙티브 /loop 세션(SPOF)이 세션 종료와 함께 조용히 사망, 감시 전무 | 세션 복구 + watchdog `orders-unconsumed` 감시 신설(오더 대기+하트비트 30분↑ → inbox 알림) | orders-poll `-Heartbeat`(소비자 생존 신호)·`-Ack`(픽업 원장) 도입, PROTOCOL §33 SPOF 명문화
- [2026-07-03 / 01:37:29 KST] | AG 좌석 하드페일 무한 백오프(07-02~) + 백오프 힌트가 오진 유도(auth/trusted-folder) | node-pty ConPTY가 Start-Job(콘솔 없는 호스트)에서 AttachConsole failed로 사망 | agy-headless.js에 `AGY_USE_CONPTY=0`(winpty) 추가, Start-Job 재현 테스트 PONG 검증, 재기동 후 cycle exit 0 | 데몬 AG 레인 env 주입 + 백오프 메시지에 실원인(ConPTY) 명시 + RUNBOOK 행
- [2026-07-03 / 01:37:29 KST] | stale open 89건 적체 → codex "stale queue hold" 공회전 커밋 스팸 + AG가 한 달 묵은 오더 재수행·반복 escalation | 오케스트레이터 dispatch가 close되지 않는 구조(single-writer상 수신자는 못 닫음) + 매 사이클 보고 강제 | 84건 batch-stale 클로즈 + 5건 응답 클로즈 | PROTOCOL §3 stale-open TTL(14일) + §5 no-op 무커밋 규칙(데몬 프롬프트 반영 — AG가 첫 사이클에서 규칙 적용 실증)
- [2026-07-03 / 05:15:00 KST] | 4-AI 라운드트립 테스트 중 AG 실작업 사망 재현 — 응답은 만들었는데 exit 1 + 미커밋 고아(중복 preview 2개) | agy-headless AGY_TIMEOUT_MS 기본 90초(주석은 180초로 거짓)가 실작업 중인 agy를 하드킬 → 재시도가 같은 작업 중복 실행 → 3회 후 AGY_EMPTY. no-op만 90초 안에 끝나 그간 은폐됨 | 기본 300초로 상향 + 데몬 AG 레인에 AGY_TIMEOUT_MS=900000·AGY_TRIES=2 주입 + AG 레인 재기동 + 고아 회수 커밋 | 래퍼-데몬 이중 타임아웃은 안쪽이 병목 — 주석-코드 불일치 교정, RUNBOOK AG행 유지
- [2026-07-03 / 05:15:00 KST] | 응답 완료된 오더에 drain 재발화(codex task 2/2 재스폰 라이브 관찰 — pool 낭비) | Count-OpenOrders가 status:open만 보고 response ref를 무시(ref-blind). single-writer상 수신자는 발신자 status를 못 닫으므로 구조적 | Count-OpenOrders를 ref-인지형으로 재작성(응답 ref가 가리키는 id/파일명은 open으로 세지 않음) | 6월 stale-89 만성화의 급성형과 동일 뿌리 — TTL(만성)+ref-인지(급성) 이중 방어 완성
