# Native Build QA Report (Android)
Date: 26.06.13 KST

## Summary
The Android native build was successfully generated and installed on the emulator, but the app is currently suffering from an ANR (App Not Responding) crash immediately after launching, when attempting to sign up or sign in.

## Issues Identified
### 1. Welcome / Sign-up Flow (✅ Verified)
- **Status:** **PASS** (Resolved ANR & OOM issues)
- **Path:** Welcome Screen -> "Create one" -> Sign up Form -> Onboarding -> Main Dashboard.

## Current Phase: Authenticated Routing & Form Validation

### 1. Authentication Gating
- **Test:** Deep-link to protected route (`secondbrain://capture`).
- **Result:** **PASS**. The Expo Router `_layout.tsx` and `index.tsx` correctly catch `!userId` and gracefully redirect the user back to `/sign-in` without crashing or throwing unhandled promise rejections. Auth context properly encapsulates the navigation stack.

### 2. Network Error Boundary & Toast Overlays
- **Test:** App load on disconnected mock Supabase host (`demo.invalid.supabase.co`).
- **Result:** **PASS** for stability (no crash), **WARN** for UX.
- **Details:** The app catches the `java.net.UnknownHostException` and displays a non-blocking UI Toast instead of a white screen of death. 
- **UX Issue Found:** The error Toast renders at `[30,2703][1314,2845]`, which overlaps and intercepts touch events intended for the bottom `1-min manual` link `[355,2851][989,2908]`. 

### 3. Sign-In / Sign-Up Form Rendering
- **Test:** Verify input fields, focus states, and scrollable containers.
- **Result:** **PASS**. `ScrollView` successfully contains the email, password, and DOB fields. The "Show password" button aligns perfectly inside the password bounds (`[1089,1541][1221,1673]`).

### 4. Deep-Link Behavior
- **Test:** Open `secondbrain://manual` when unauthenticated.
- **Result:** **WARN** for Intent Handling. The `adb` intent was delivered to the existing `MainActivity` but did not effectively render the manual screen, potentially due to the Auth intercept or Expo Router deep-link scheme mismatch.

## Screenshots Captured
- `screen_firstglimpse3.png`: Welcome Screen.
- `screen_firstglimpse4.png`: ANR Dialog on the Welcome Screen.

## Next Steps
- Android 앱 기본 계정 생성 및 메인 대시보드 진입 검증 완료.
- 추가적인 인앱 기능 검수 대기.
