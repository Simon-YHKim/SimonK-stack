# Architecture Patterns — 상세 레퍼런스

## Contents

1. [레이어링 규칙](#레이어링-규칙)
2. [네이밍 컨벤션 표](#네이밍-컨벤션-표)
3. [Anti-pattern 갤러리](#anti-pattern-갤러리)
4. [리팩토링 트리거](#리팩토링-트리거)
5. [의존성 시각화 도구](#의존성-시각화-도구)

---

## 레이어링 규칙

### 단방향 의존성의 의미

```
[ Page Layer    ]  ← 사용자 진입점, route 처리
    ↓ import only
[ Feature Layer ]  ← 도메인 로직 (auth, billing, profile)
    ↓ import only
[ Shared Layer  ]  ← 재사용 컴포넌트, 유틸
    ↓ import only
[ Util Layer    ]  ← 순수 함수, 프레임워크 독립
```

- **상위 → 하위만 허용**: page는 feature, shared, util을 모두 사용 가능
- **동위 → 금지**: feature-a가 feature-b를 직접 부르면 안 됨. shared로 추출
- **하위 → 상위 금지**: util이 feature를 부르면 의존 방향이 깨짐 → 콜백 패턴으로 위로 위임

### Shared 모듈의 책임

shared/는 도메인 무관해야 한다. "auth에서만 쓰이는 헬퍼"는 shared가 아니라 feature/auth/lib에 둔다.

기준 질문:
- 다른 두 feature가 동시에 쓸 가능성이 있나? → shared
- 한 feature 내부에서만 쓰이나? → feature/<domain>/lib

### Adapter 레이어

외부 의존성(Stripe, Supabase, Toss)은 adapters/로 격리. feature는 adapter의 인터페이스만 알고 구현체는 모름.

```ts
// ❌ feature가 외부 SDK 직접 import
import Stripe from 'stripe'

// ✅ adapter 인터페이스만 import
import { paymentClient } from '@/adapters/payment'
```

---

## 네이밍 컨벤션 표

| 카테고리 | 컨벤션 | 좋은 예 | 나쁜 예 |
|---|---|---|---|
| 파일 (TS/JS) | kebab-case | `user-profile.ts` | `userProfile.ts`, `UserProfile.ts` |
| React 컴포넌트 파일 | PascalCase | `UserProfile.tsx` | `userProfile.tsx`, `user-profile.tsx` |
| 훅 파일 | use- prefix | `use-auth.ts` | `auth-hook.ts` |
| 타입 파일 | types.ts 또는 .types.ts | `user.types.ts` | `userTypes.ts` |
| 함수 | camelCase 동사 시작 | `getUserById`, `parseDate` | `user_get`, `date` |
| boolean 변수 | is/has/can 시작 | `isLoading`, `hasAccess` | `loading`, `access` |
| 이벤트 핸들러 | handle- prefix | `handleSubmit`, `handleClick` | `submit`, `onSubmit` (prop은 OK) |
| 상수 | UPPER_SNAKE | `MAX_RETRY = 3` | `maxRetry` |
| 인터페이스 | I prefix 또는 그냥 PascalCase | `IUserRepo` 또는 `UserRepo` | 일관성 없는 혼용 |
| 디렉토리 | kebab-case 단수 | `feature/`, `util/` | `Features/`, `utils/` |

### 한국어 프로젝트 추가 규칙

- 파일/변수명은 영어로
- 주석은 한국어 OK, 공식 문서는 한/영 병기
- 도메인 용어는 README나 GLOSSARY에 한/영 매핑 표 작성

---

## Anti-pattern 갤러리

### Anti-pattern 1: God file

```ts
// ❌ src/utils.ts (3000 lines, everything dumped here)
export function formatDate() {...}
export function parseUrl() {...}
export function calculateTax() {...}
// ... 200+ functions
```

**해결**: 도메인별로 분리. `src/util/date.ts`, `src/util/url.ts`, `src/feature/billing/lib/tax.ts`.

### Anti-pattern 2: Circular dependency

```ts
// a.ts
import { foo } from './b'
export const bar = () => foo()

// b.ts
import { bar } from './a'  // ← 순환
export const foo = () => bar()
```

**해결**: 공통 의존을 c.ts로 추출. a, b는 c만 import.

### Anti-pattern 3: Upward dependency

```ts
// shared/ui/Button.tsx
import { useAuth } from '@/feature/auth/hooks'  // ❌ shared가 feature를 의존
```

**해결**: Button은 props로 콜백을 받음. 상위가 useAuth를 wire함.

### Anti-pattern 4: 100-line function

```ts
function processOrder(order) {
  // validation 30 lines
  // pricing calculation 25 lines
  // discount application 20 lines
  // tax calculation 15 lines
  // database persist 20 lines
}
```

**해결**: 5개 함수로 분리. `validateOrder`, `calculatePrice`, `applyDiscounts`, `calculateTax`, `persistOrder`. processOrder는 오케스트레이션만.

### Anti-pattern 5: 임시 파일이 영구화

```
src/
├── temp.ts           # 6개월 전 만든 "임시"
├── newUtils.ts       # 어떤 게 더 새 것?
└── utils-old.ts      # 백업?
```

**해결**: 임시 파일 금지. 백업은 git이 한다. `temp`/`old`/`new` prefix 금지.

### Anti-pattern 6: Magic file location

```
src/components/UserProfile/UserProfileService.ts
```

UI 컴포넌트 폴더에 service가 있음. UI와 비즈니스 로직 섞임.

**해결**: UI는 components에, service는 features/profile/services에.

---

## 리팩토링 트리거

| 신호 | 액션 |
|---|---|
| 함수 > 40 lines | 책임 분리 |
| 파일 > 300 lines | 도메인별 분리 검토 |
| 파일 > 500 lines | 강제 분리 |
| if/for 중첩 > 3 | early return / guard clause |
| 함수 인자 > 5 | 객체 인수로 묶기 |
| 동일/유사 코드 3회 반복 | 추출 (DRY) |
| 클래스 메서드 > 10 | 책임 분리 (SRP 위반 의심) |
| import 라인 > 20 | 한 파일이 너무 많은 일을 함 |

---

## 의존성 시각화 도구

### madge (TypeScript/JavaScript)

```bash
# 순환 의존 탐지
npx madge --circular src/

# 의존 그래프 시각화 (graphviz 필요)
npx madge --image graph.png src/

# JSON 출력
npx madge --json src/ > deps.json
```

### dependency-cruiser

```bash
npx depcruise --validate .dependency-cruiser.js src
```

`.dependency-cruiser.js`에 레이어 규칙을 코드로 강제 가능.

### Python

```bash
# pydeps
pydeps src/ --max-bacon 5 -o deps.svg

# import-linter (계약 강제)
lint-imports
```

`importlinter.ini`에 레이어 계약 작성:

```ini
[importlinter:contract:layered-arch]
name = Layered architecture
type = layers
layers =
    api
    services
    repositories
    models
```

### Go

```bash
# 순환 의존 탐지 (go vet은 컴파일러가 거부함)
go list -deps ./...
```

Go는 컴파일러가 순환을 거부하므로 사후 검사 불필요.

---

## 통합 체크 (CI에 추가 권장)

```bash
#!/usr/bin/env bash
# .github/workflows/code-health.yml 안에 추가

set -e
echo "=== Circular deps ===" && npx madge --circular src/
echo "=== Unused exports ===" && npx ts-unused-exports tsconfig.json
echo "=== Large files ===" && \
  find src -name "*.ts" | xargs wc -l | sort -rn | head -10 | \
  awk '$1 > 500 {print "FAIL: " $2 " has " $1 " lines"; exit 1}'
echo "✅ Code health PASS"
```
