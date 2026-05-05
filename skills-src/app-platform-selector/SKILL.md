---
name: app-platform-selector
description: "Use when the user needs to decide between hybrid app, PWA, or native development—triggers "하이브리드 앱 좋을까", "PWA vs 네이티브", "앱 플랫폼 선택", "웹앱으로 할까", "React Native vs Flutter", "hybrid or native", "should I build a PWA", "app wrapper rejection". Produces platform decision (Hybrid/PWA/Native) with pros-cons analysis, store approval strategy for web-wrapped apps, and technology recommendation (React Native/Flutter/Expo/Capacitor)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# app-platform-selector

Hybrid/PWA/Native 판단 + 스토어 통과 전략.

## 발동 조건

- "하이브리드 앱 좋을까", "PWA vs 네이티브", "앱 플랫폼 선택"
- "웹앱으로 스토어 등록 가능해?", "React Native vs Flutter"
- stack-architect에서 모바일 결정 시 호출

## Decision Matrix

| 기준 | PWA | Hybrid (Capacitor/Expo) | Cross-platform (RN/Flutter) | Native (Swift/Kotlin) |
|---|---|---|---|---|
| 개발 속도 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 성능 | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 스토어 등록 | ❌~△ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 네이티브 API | 제한적 | 플러그인 | 대부분 | 전체 |
| 업데이트 속도 | 즉시 (웹) | OTA 가능 | OTA 가능 | 스토어 심사 |
| 1인 개발 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |

## Decision Tree

```
스토어 등록 필수?
├─ NO → PWA (설치 프롬프트, 오프라인, 푸시)
└─ YES
    ├─ 네이티브 API 많이 필요? (카메라, 센서, 결제)
    │   ├─ YES → React Native (JS 생태계) or Flutter (성능)
    │   └─ NO → Hybrid (Capacitor + 기존 웹 코드)
    └─ 최고 성능 필수? (게임, 영상편집)
        └─ YES → Native (Swift + Kotlin)
```

## ⚠️ 웹 래퍼 리젝 방지 전략

Apple 4.2 "Minimum Functionality" 리젝 사유:
> "Your app is primarily a repackaged website"

**통과 전략**:

| 방법 | 설명 |
|---|---|
| 네이티브 기능 추가 | 푸시 알림, 위젯, Share Extension |
| 오프라인 모드 | 기본 기능이 오프라인에서도 동작 |
| 딥 인터랙션 | 제스처, 햅틱, 네이티브 네비게이션 |
| 고유 콘텐츠 | 앱 전용 기능 1개 이상 |
| Capacitor 플러그인 | Camera, Filesystem, LocalNotification |

**절대 안 되는 것**:
- WKWebView 하나에 URL 로드만 (100% 리젝)
- 웹과 100% 동일한 경험 (차별화 없음)
- 로그인 후 빈 WebView

## 기술 스택 추천

| 상황 | 추천 | 이유 |
|---|---|---|
| 기존 React 웹 있음 | Capacitor (Ionic) | 웹 코드 재사용 극대화 |
| 기존 Next.js 앱 | Expo (React Native) | React 경험 활용 |
| 새로 시작 + 성능 중요 | Flutter | 자체 렌더링, 일관된 UX |
| 새로 시작 + JS 생태계 | React Native (Expo) | 커뮤니티 + 라이브러리 풍부 |

## Related Skills

- `stack-architect` — 전체 아키텍처 내 모바일 위치
- `store-launcher` — 선택된 플랫폼으로 스토어 출시
- `deploy-configurator` — OTA 업데이트 + CI/CD
