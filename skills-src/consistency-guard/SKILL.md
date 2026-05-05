---
name: consistency-guard
description: "Use when the user needs to maintain data or UI consistency across a service—triggers "일관성 유지", "데이터 스키마 검증", "JSON 일관성", "config 관리", "design token", "consistency check", "schema validation", "maintain uniformity". Produces a JSON-schema-based consistency framework that determines which parts of the service need strict consistency (API contracts, design tokens, config) vs flexible parts, with automated validation rules."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# consistency-guard

서비스 일관성을 JSON schema 기반으로 판단하고 강제하는 skill.

## 발동 조건

- "일관성 유지 필요한 부분 확인해줘", "스키마 검증"
- "JSON 일관성", "config 관리", "design token 정리"
- 프로젝트 성장 시 일관성 문제 감지될 때

## 일관성 필요 여부 판단

### 반드시 일관성 필요 (strict)

| 영역 | 이유 | 강제 방법 |
|---|---|---|
| API Response 형태 | 클라이언트 파싱 깨짐 | JSON Schema + 타입 생성 |
| Design Tokens | UI 불일치 | tokens.json + 변환 파이프라인 |
| Error Codes | 에러 핸들링 로직 | enum + 코드북 |
| Config/ENV | 환경별 동작 차이 | schema validation on boot |
| DB Migration | 데이터 무결성 | 스키마 버전 관리 |
| i18n Keys | 번역 누락 | key 완전성 검사 |

### 일관성 불필요 (flexible)

| 영역 | 이유 |
|---|---|
| 내부 유틸 함수 시그니처 | 리팩토링 자유도 |
| 주석/문서 형식 | 개발자 자율 |
| 테스트 데이터 | 변동 허용 |
| 로그 메시지 텍스트 | 가독성 우선 |

## 자동 검증 프레임워크

```json
// consistency-rules.json
{
  "api_responses": {
    "enforce": true,
    "method": "json-schema",
    "schema_dir": "schemas/api/"
  },
  "design_tokens": {
    "enforce": true,
    "method": "tokens.json",
    "source": "design/tokens.json"
  },
  "error_codes": {
    "enforce": true,
    "method": "enum",
    "source": "src/constants/errors.ts"
  },
  "env_config": {
    "enforce": true,
    "method": "zod-schema",
    "source": "src/config/env.ts"
  }
}
```

## 산출물

- `consistency-rules.json` — 어디에 일관성이 필요한지 명세
- CI에서 자동 검증하는 스크립트
- 위반 시 명확한 에러 메시지

## Related Skills

- `code-health-guard` — 코드 구조 일관성 (import, naming)
- `analytics-integrator` — 이벤트 택소노미 일관성
- `tag-manager-integrator` — 태그 명명 일관성
