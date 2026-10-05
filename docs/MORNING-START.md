# Morning Start — 4시간 뒤 출근해서 읽을 것

> **은퇴한 설치 안내 (허브 D-87, 2026-10-05).** 이 문서가 설명하던 자동 설치는 더 이상 동작하지 않는다. SessionStart 훅의 bootstrap(Gstack clone·`bun install`·스킬 복사·instincts seed·`~/.claude/CLAUDE.md` 설치), 마커 파일(`~/.claude/.simon-stack-installed`)을 지워 다시 설치하는 방법, `scripts/install.sh` git clone 설치가 모두 은퇴했다. SessionStart 훅은 이제 읽기 전용 안내만 출력하고 아무것도 쓰지 않는다. 예전 설치·확인·문제 해결 본문은 git 이력에 있다.

## 지금 설치하는 법

- 사용자: [README 3절 설치](../README.md#3-설치) — 마켓플레이스 다섯 플러그인(`dist` 브랜치).
- 이 PC(flat 설치)와 개발: [README 11절 개발자 안내](../README.md#11-개발자-안내) — `pwsh -File scripts/windows/update-local.ps1`(미리보기, `-Apply`로 설치).
- 옛 설치 스크립트: [`_archive/legacy-install/`](../_archive/legacy-install/README.md).

---

## ⚠️ 출근 전 한 번만 할 일 (당시 기록)

### (b) 스테일 브랜치 삭제 (옵션, 청소용)
https://github.com/Simon-YHKim/SimonK-stack/settings/branches 에서:
- `claude/create-skill-set-BZBaN` — 쓰레기통 아이콘 클릭 (로컬은 이미 삭제됨. 원격은 프록시 403 때문에 CLI 로 못 지웠음)
- `claude/create-claude-skill-Jt63X` — 이미 CLI 로 삭제됨 (로컬/원격 둘 다)

### (c) 노출된 Stitch API 키 로테이션
이전 세션 transcript 에 키가 평문으로 남아있음. Google Stitch 대시보드에서 해당 키 revoke + 신규 발급.

((a) default branch 전환은 SessionStart hook 로딩을 위한 설치 단계였으므로 위 은퇴 안내로 대체했다.)

---

## 🎯 사용 시나리오 예시

### 시나리오 1: 새 앱 프로젝트 시작
```
나: "카카오톡 로그인 기반 한국 부동산 매물 크롤링 앱 만들고 싶어"

Claude: [app-dev-orchestrator 발동]
  단계 0. 인터뷰: 플랫폼? 타깃? 레포? 예산?
  단계 1. /office-hours 로 YC 6문 진행
  단계 2. simon-research 로 경쟁 제품 3종 비교
  ...
```

### 시나리오 2: 보안 감사
```
나: "배포 전에 보안 점검 싹 해줘"

Claude: [security-orchestrator 발동]
  Step 1. security-checklist: RLS / 구독 / RateLimit / 예산 4대 감사
  Step 2. authz-designer: IDOR 스캔, 권한 상승 테스트
  Step 3. paid-api-guard: 결제·SMS API 6층 방어 점검
  Step 4. /cso comprehensive: 인프라·시크릿·공급망 감사
  Step 5. /codex challenge: 적대적 리뷰
  → docs/security/<date>-SUMMARY.md 통합 리포트
```

### 시나리오 3: 같은 실수 반복 방지
```
나: "이거 저번에도 그랬잖아"

Claude: [simon-instincts 발동]
  ~/.claude/instincts/mistakes-learned.md 에 즉시 append
  - 날짜 / 증상 / 원인 / 예방책
  다음 세션부터 자동 로드
```

---

## 🔧 문제 해결

설치·업데이트·스킬 미발동 문제는 [README 9절 문제 해결](../README.md#9-문제-해결)을 본다. 위 은퇴 안내 이전의 확인 명령(훅 로그, 마커 파일, 강제 재설치, `~/.claude.bak-*` 복원)은 git 이력에 있다.

---

## 📚 추가 자료

- `README.md` — 레포 overview, 설치(3절), 개발자 안내(11절)
- `docs/INSTALL.md` — 설치·배포 절차와 검증 기록
- `.claude/skills/INDEX.md` — skill 카테고리 맵
- `.claude/instincts/` — 4개 누적 학습 파일
- `templates/CLAUDE.md` — 글로벌 CLAUDE.md 템플릿

---

## 🎁 4시간 동안 Claude 가 한 일 요약 (당시 기록 — 설치 관련 항목은 D-87로 은퇴)

- ✅ Gstack 36 skill 런타임 설치 + `bun install`
- ✅ simon-stack 13 skill 생성 (orchestrator · security · method · tools)
- ✅ 4 instincts seed (mistakes · patterns · korean · tool-quirks)
- ✅ `~/.claude/CLAUDE.md` 템플릿 (Boris 원칙 + skill stack 맵)
- ✅ SessionStart hook 2개 — 레포 bootstrap + user instincts 요약
- ✅ `.claude/settings.json` 에 hook 등록
- ✅ `main` 브랜치 생성 + 푸시 + 로컬 stale 브랜치 정리
- ✅ `scripts/install.sh` 수동 설치 스크립트
- ✅ `docs/INSTALL.md`, `README.md`, 이 문서
- ✅ 빈 HOME 에서 end-to-end 설치 시뮬레이션 통과 (56 skills)

**주무시는 동안 수고하셨습니다. 좋은 출근 되세요.** 🌅
