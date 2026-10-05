---
name: code-health-guard
description: "Use when the user asks to check code structure, prevent spaghetti code, organize files, or refactor architecture—triggers \"코드 구조 점검\", \"아키텍처 확인\", \"파일 구조 정리\", \"레이어 분리\", \"spaghetti check\", \"dependency graph\", \"structured code\", \"file organization\". Produces a proactive checklist (file placement, naming, import direction, function size, duplicate detection) + reactive scans (circular deps via madge, dead exports via ts-unused-exports, large file flagging). Enforces unidirectional layer dependencies, single-responsibility files, and shared module export-only rule. Works alongside refactor and simon-tdd."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon-stack
---

# code-health-guard

스파게티 코드를 사전 방지하고 구조화된 코드 작성을 강제하는 skill.

## 핵심 원칙 (Korean Medium 출처)

1. **단방향 의존성** — 레이어는 인접 하위 레이어만 import. 상위 import 절대 금지
2. **책임 분리** — 1 file = 1 concern. 파일이 두 가지 일을 하면 분리
3. **shared 모듈은 export only** — feature/, page/ 에서 shared/ import는 OK. 그 반대 절대 금지
4. **readability > cleverness** — 영리한 한 줄보다 읽기 쉬운 다섯 줄

## Proactive Checks — 코드 작성 *전*

### 1. File placement decision tree

```
새 파일 만들기 전 질문:
  - 특정 기능에만 쓰이나? → src/features/<domain>/
  - 여러 feature가 공유하나? → src/shared/
  - 타입 정의만? → src/types/
  - 환경별 설정? → src/config/
  - 외부 API 어댑터? → src/adapters/<vendor>/
```

### 2. Naming conventions

| 종류 | 규칙 | 예시 |
|---|---|---|
| 파일 (TS/JS) | kebab-case | `user-profile.ts` |
| React 컴포넌트 | PascalCase 파일 | `UserProfile.tsx` |
| 함수/변수 | camelCase | `getUserProfile` |
| 타입/인터페이스 | PascalCase | `UserProfile`, `IUserRepo` |
| 상수 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 디렉토리 | kebab-case 단수 | `feature/`, `util/` |

### 3. Import direction check

```
허용:
  page/ → feature/ → shared/ → util/
  feature/ → shared/

금지:
  shared/ → feature/    (상위 의존)
  feature-a/ → feature-b/   (peer 의존, shared/로 추출)
  순환 의존 (A → B → A)
```

### 4. Function size

- 함수 본문 > 40 lines = 분리 후보
- 중첩 if/for > 3 depth = 분리 후보
- arguments > 5개 = 객체 인수로 묶기

### 5. Duplicate detection

코드 작성 전 `grep`/`Glob`으로 유사 패턴 검색. 발견 시 `shared/`로 추출.

## Reactive Checks — 기존 코드 진단

### 순환 의존성 스캔

```bash
bash skills-src/code-health-guard/scripts/check-circular-deps.sh
# 또는 madge가 설치돼 있으면:
npx madge --circular src/
```

### 사용되지 않는 export

```bash
# TS 프로젝트
npx ts-unused-exports tsconfig.json

# JS 프로젝트
npx unimported
```

### 큰 파일 식별

```bash
find src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.py" \) \
  -exec wc -l {} + | sort -rn | head -20
```

300줄 초과 파일은 분리 후보. 500줄 초과는 강제 분리.

## File Organization Template

```
src/
├── features/
│   ├── auth/             # 인증 도메인
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types.ts
│   ├── billing/
│   └── profile/
├── shared/
│   ├── ui/               # 공통 UI 컴포넌트
│   ├── hooks/            # 공통 훅
│   ├── lib/              # 유틸리티
│   └── api/              # API 클라이언트
├── types/                # 글로벌 타입
├── config/               # env 분기 설정
└── adapters/             # 외부 통합 (Stripe, Supabase 등)
    ├── stripe/
    └── supabase/
```

## 의무 적용 시점

- **코드 작성 전**: Proactive Checks 5개 모두 통과 확인
- **PR 전**: Reactive Checks 3개 모두 실행
- **`app-dev-orchestrator` step 13.5**: simon-tdd와 함께 호출됨

상세 패턴은 [references/architecture-patterns.md](references/architecture-patterns.md) 참조.

## Anti-patterns

- ❌ 새 파일을 어디 둘지 결정 없이 일단 작성
- ❌ shared/에서 feature/ import (상위 의존)
- ❌ 함수 100줄, 중첩 5단
- ❌ 중복 코드 발견하고 "나중에 정리" — 다음에 절대 안 함
- ❌ "임시"라며 src/ 루트에 파일 던지기
- ❌ 순환 의존을 기능 추가로 우회 (분리해야 함)

## Related skills

- `refactor` — 발견된 문제를 실제로 리팩토링
- `simon-tdd` — 리팩토링 안전망 (테스트 통과 보장)
- `/review` — PR 사전 리뷰에 통합
