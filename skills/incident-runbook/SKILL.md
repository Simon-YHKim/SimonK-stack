---
name: incident-runbook
description: "Use when the user reports a live outage or needs to run an incident—triggers \"인시던트\", \"장애 대응\", \"서비스 죽었어\", \"프로덕션 내려갔어\", \"롤백 결정\", \"롤백할까\", \"on-call\", \"긴급 대응\", \"postmortem 준비\", \"incident\", \"production down\", \"should I roll back\", \"page me\". Produces a SEV severity call (impact × scope), a rollback / feature-flag-kill decision tree, status + comms templates, a live incident loop to drive recovery, and a clean handoff to postmortem. Built for a solo builder recovering at 3 AM: every step is a checklist or a decision tree, no judgment calls left unframed."
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# incident-runbook

라이브 인시던트를 진단 → 완화 → 복구 → 핸드오프까지 끌고 가는 on-call 런북.
혼자 새벽에 깨서 대응하는 솔로 빌더 가정 — 매 단계는 **체크리스트 또는 결정트리**이고, 판단을 떠넘기지 않는다.

## 발동 조건

- "인시던트", "장애 대응", "서비스 죽었어", "프로덕션 내려갔어", "긴급"
- "롤백 결정", "롤백할까", "이거 끌까"
- "on-call", "지금 깨워졌어", "알림 떴어"
- "postmortem 준비", "사후 보고서"
- `/incident-runbook`

## 첫 60초 — 안정화 우선

장애 중에는 원인 분석보다 **영향 차단**이 먼저다. 디버깅 충동을 누르고 순서대로:

1. **사실 확인** — 진짜 죽었나? 본인 환경/캐시 문제 아닌가? (다른 네트워크·시크릿창에서 재현)
2. **타임스탬프 기록** — 감지 시각을 `T0`로 남긴다. 모든 후속 기록의 기준.
3. **최근 변경 확인** — `git log --oneline -10`, 마지막 배포/머지 시각. 대부분의 장애는 최근 변경에서 온다.
4. **SEV 판정** (아래 표) → 판정에 따라 완화 경로 분기.

> 원칙: **완화 먼저, 원인 분석은 나중.** 사용자 영향을 멈춘 뒤 근본 원인을 판다.

## SEV 사다리 (영향 × 범위)

| SEV | 영향 | 범위 | 대응 | 목표 완화 |
|---|---|---|---|---|
| SEV1 | 핵심 기능 전체 불능 / 데이터 손실·유출 위험 | 전체 사용자 | 즉시 모든 일 중단, 가장 빠른 완화(롤백/킬) 실행 | 최대한 빨리 |
| SEV2 | 핵심 플로우 일부 불능 (로그인·결제·핵심 화면) | 다수 사용자 | 우선 대응, 완화 후 원인 분석 | 30분 내 완화 착수 |
| SEV3 | 부가 기능 저하 / 회피 가능 | 일부 사용자 | 정규 시간 내 대응, 모니터링 강화 | 당일 |
| SEV4 | 경미·미관 / 영향 거의 없음 | 소수·엣지 | 백로그로, 인시던트 종료 | 정규 작업 |

**판정 규칙 (둘 중 높은 쪽 채택):**
- 데이터 손실·유출·과금 오류 의심 → 최소 SEV1.
- 결제·인증 경로가 막히면 → 최소 SEV2.
- "회피 방법이 있나?" 가 yes 면 한 단계 낮춰도 된다.
- 애매하면 **한 단계 높게** 잡고 시작 — 내리는 건 쉽고, 늦게 올리는 건 비싸다.

SEV1/2는 즉시 상태 공지를 띄운다 (아래 comms 템플릿).

## 완화 결정트리 — 롤백 vs feature-flag-kill vs 핫픽스

```
최근 배포/머지가 원인으로 의심되나?
├─ Yes → 그 변경이 feature flag 뒤에 있나?
│        ├─ Yes → [FLAG KILL] 플래그 OFF. 가장 안전·가장 빠름. 배포 불필요.
│        └─ No  → 직전 배포로 롤백 가능한가? (이전 빌드/커밋 존재)
│                 ├─ Yes → [ROLLBACK] 직전 정상 배포로 되돌린다.
│                 └─ No  → [HOTFIX] 최소 변경 핫픽스 (아래 핫픽스 규칙)
└─ No (인프라/외부 의존성 의심)
         ├─ 외부 API/서드파티 다운? → [DEGRADE] 해당 기능만 graceful 차단 + 상태 공지
         ├─ DB/마이그레이션? → [DB 경로] 아래 별도 주의
         └─ 트래픽/리소스? → 스케일·rate-limit, 캐시 확인
```

**선택 우선순위 (빠르고 안전한 순):** FLAG KILL > ROLLBACK > DEGRADE > HOTFIX.

- **FLAG KILL**: 코드 변경이 플래그 뒤에 있으면 항상 1순위. 배포 파이프라인을 안 타므로 초 단위로 효과. 끈 직후 영향 사라지는지 확인.
- **ROLLBACK**: 플랫폼 즉시 롤백 우선 (Vercel/EAS Update/Cloudflare 등 직전 배포 재활성). git revert 후 재배포는 그다음. 되돌린 시점·버전을 기록.
- **HOTFIX**: 새벽엔 위험. 적용 전 반드시 결정트리의 위 두 경로가 불가능함을 확인. 핫픽스 규칙:
  - 변경 한 곳, 한 줄에 가깝게. 리팩터링 금지.
  - 가능하면 로컬/프리뷰에서 재현→수정 확인 후 배포.
  - 배포 후 효과 확인 전까지 인시던트 안 닫는다.
- **DB 경로 (위험)**: 스키마 롤백은 데이터 손실 가능. 파괴적 마이그레이션 되돌리기 전 **사용자 confirm 필수**. 가능하면 코드 롤백으로 회피하고 스키마는 그대로 둔다. `DROP`/`TRUNCATE`/`reset` 류는 절대 자동 실행 금지.

> 환경/플랫폼별 정확한 롤백·플래그 명령은 프로젝트마다 다르다. 모르면 `deploy-configurator` 산출물(롤백 방법 문서)이나 프로젝트 CLAUDE.md를 먼저 확인하고, 없으면 사용자에게 묻는다. 시크릿은 항상 env에서 — 명령에 키를 박지 않는다.

## 상태 · 커뮤니케이션

대응자가 막혀서 침묵하면 사용자는 더 불안하다. SEV1/2는 **완화 시작 시점**과 **해결 시점**에 공지한다.

- 첫 공지: 무엇이 영향받는지 + 인지했다는 사실 + 다음 업데이트 시각. 원인 추측 금지.
- 업데이트: 약속한 시각에 진전 없어도 "조사 중, 다음 X시" 라고 보낸다. 침묵이 최악.
- 해결: 복구 확인 후 종료 공지. 사과는 짧게, 보상·후속은 postmortem 후.

템플릿: `templates/status-update.md` (공개 상태 공지), `templates/comms-internal.md` (내부/본인 타임라인 메모).

## 라이브 인시던트 구동 루프

완화 경로를 골랐으면 닫힐 때까지 이 루프를 돈다:

1. **타임라인 시작** — `scripts/incident-log.sh "<제목>" SEV2` 로 인시던트 로그 파일 생성 (T0·SEV 기록).
2. **완화 실행** — 결정트리에서 고른 액션 1개만. 동시에 여러 개 건드리지 않는다 (효과 구분 불가).
3. **효과 측정** — 액션 직후 실제로 영향이 사라졌는지 확인. 측정 방법:
   - 사용자 경로 직접 재현 (브라우저/앱). 가능하면 `browse`/`qa` 로 핵심 플로우.
   - 에러율·로그 (Supabase `get_logs`, Sentry, 플랫폼 로그) 감소 확인.
   - "고쳐졌겠지" 금지 — 신호로 확인.
4. **기록** — 한 줄씩 `scripts/incident-log.sh --note "<무엇을 했고 결과>"`. 새벽 기억은 못 믿는다, 다 적는다.
5. **안정 or 다음 액션** — 영향 사라졌으면 모니터링 단계로. 아니면 결정트리 다음 경로로 돌아간다.

완화 후 **최소 15분 모니터링** 하고 재발 없을 때 종료. (재발하면 SEV 한 단계 올린다.)

## 종료 → postmortem 핸드오프

인시던트가 닫히면 즉시 **사실만** postmortem 골격을 만든다 (분석은 나중, 기억은 지금 신선).

- `scripts/incident-log.sh --close` → 타임라인을 `templates/postmortem.md` 골격에 채워 `docs/incidents/INCIDENT-<날짜>-<slug>.md` 초안 생성.
- 채워야 할 핵심: 타임라인(T0~복구), 영향 범위, 근본 원인(모르면 "조사 중"), 완화 방법, **재발 방지 액션 아이템**.
- 비난 없는(blameless) 톤 — 사람이 아니라 시스템의 구멍을 본다.
- 깊은 회고·트렌드는 `retro` 로, 재발 방지가 코드 헬스 이슈면 `code-health-guard` 로 넘긴다.

## 검증 체크리스트 (종료 전 확인)

- [ ] 사용자 영향이 실제로 사라졌는가 (신호로 확인, 추측 아님)
- [ ] 완화 액션·시각·버전이 타임라인에 기록됨
- [ ] SEV1/2였다면 해결 공지 발송
- [ ] 임시 완화(플래그 OFF 등)가 남아 있다면 후속 액션 아이템에 명시
- [ ] postmortem 초안 생성 + 재발 방지 액션 1개 이상
- [ ] 파괴적 작업(DB 롤백 등) 했다면 사용자 confirm 받았음

## Related Skills

- `canary` — 배포 직후 이상 감지. 인시던트를 *먼저* 잡아 SEV를 낮춰준다.
- `release-health-guard` — 릴리스 건강 지표 모니터링 (없으면 `health` + `canary` 조합으로 대체).
- `retro` — 인시던트 종료 후 트렌드·주간 회고로 확장.
- `deploy-configurator` — 롤백 방법·환경변수·모니터링 설정 (완화 경로의 전제 인프라).
