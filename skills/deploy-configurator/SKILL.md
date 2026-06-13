---
name: deploy-configurator
description: "Use when the user asks to set up deployment, hosting, or CI/CD—triggers \"배포 설정\", \"Vercel 세팅\", \"Cloudflare 배포\", \"CI/CD 만들어줘\", \"Docker 배포\", \"setup hosting\", \"deploy to production\", \"configure CI\". Produces deployment configuration for selected platform (Cloudflare/Vercel/Fly.io/Railway), CI/CD pipeline (GitHub Actions), custom domain + SSL, environment variable management, and monitoring/alerting setup."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# deploy-configurator

배포 플랫폼 설정 + CI/CD + 모니터링을 구성하는 skill.

## 발동 조건

- "배포 설정해줘", "Vercel 세팅", "Cloudflare Workers 배포"
- "CI/CD 만들어줘", "Docker 배포", "GitHub Actions"
- app-dev-orchestrator 배포 단계에서 호출

## 플랫폼 선택

```
앱 유형?
├─ 정적 사이트 / SSG
│   └─ Cloudflare Pages (무료, 글로벌 CDN)
├─ Next.js / SSR
│   ├─ Vercel (최적화, 간편)
│   └─ Cloudflare Pages (edge runtime)
├─ API / 백엔드
│   ├─ 컨테이너 → Fly.io, Railway
│   ├─ 서버리스 → Cloudflare Workers, AWS Lambda
│   └─ BaaS → Supabase Edge Functions
├─ 풀스택 (DB 포함)
│   ├─ Railway (PostgreSQL 내장)
│   ├─ Fly.io + Supabase
│   └─ AWS / GCP (규모 큰 경우)
└─ 모바일 앱 빌드
    ├─ EAS Build (Expo)
    └─ Fastlane + GitHub Actions
```

## CI/CD 표준 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      # Platform-specific deploy step
```

## 환경변수 관리

| 방법 | 적합한 경우 |
|---|---|
| 플랫폼 UI (Vercel/Cloudflare) | 소규모, 간편 |
| GitHub Secrets + Actions | CI/CD 연동 |
| Doppler / Infisical | 팀, 다중 환경 |
| AWS Secrets Manager | 엔터프라이즈 |

**원칙**: `.env`는 `.gitignore`에 반드시 포함. 시크릿은 절대 하드코딩 금지.

## 모니터링 스택

| 영역 | 도구 | 용도 |
|---|---|---|
| 에러 | Sentry | 런타임 에러 추적 |
| 업타임 | BetterStack / UptimeRobot | 다운 알림 |
| 성능 | Vercel Analytics / Cloudflare | Core Web Vitals |
| 로그 | Axiom / Datadog | 구조화 로그 |
| 비용 | 플랫폼 billing alert | 예산 초과 방지 |

## 검증 체크리스트

- [ ] PR 시 자동 Preview Deploy
- [ ] main push 시 Production Deploy
- [ ] 환경변수 분리 (dev/staging/prod)
- [ ] 커스텀 도메인 + SSL 자동
- [ ] Health check endpoint (`/api/health`)
- [ ] Rollback 방법 문서화
- [ ] Sentry/에러 추적 연결

## Related Skills

- `store-launcher` — CI에서 스토어 자동 업로드 연동
- `analytics-integrator` — 배포 후 분석 도구 활성화
- `revenue-scenario-tester` — 프로덕션 환경 시나리오 테스트

