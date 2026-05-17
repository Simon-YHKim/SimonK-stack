# Eject Button v1.6.3 — Lessons Learned

> Date: 2026-05-17
> Source: end-to-end release audit + Play Store production prep
> Project: Simon-YHKim/eject-button (com.simonykim.ejectbutton)

---

## 1. AdMob native ad — MediaView is mandatory, ≥120×120dp for video

**Symptom**: AdMob native ad validator gave 2-stage failure:
1. "MediaView not used for main image or video asset" (hard error, blocks ad delivery)
2. "MediaView is too small for video" (warning, ≥120×120dp required for proper video render)

**Root cause**: Compact 1-row banner used only `iconView (ImageView, 48dp)`. The main asset (`ad.mediaContent` — image or video) needs `MediaView`, not `ImageView`. Even if you don't visually need a "big image" slot, you must bind a MediaView for the SDK to deliver image/video ads properly.

**Fix pattern**:
```kotlin
val mediaView = MediaView(ctx).apply {
    layoutParams = LinearLayout.LayoutParams(dp(120), dp(120)).apply {
        marginEnd = dp(10)
    }
    minimumWidth = dp(120)
    minimumHeight = dp(120)
    setImageScaleType(ImageView.ScaleType.CENTER_CROP)
}
adView.mediaView = mediaView
// setNativeAd(ad) auto-binds ad.mediaContent — no manual drawable in update lambda
```

**Trade-off**: Banner row grows from ~60dp to 120dp+ tall. Acceptable for video-ad-revenue + policy compliance.

---

## 2. Android adaptive launcher icon — 20-PNG pipeline

**Pattern**: Replacing the launcher icon requires regenerating ALL 20 PNGs:
- **5 densities**: mdpi(48/108) · hdpi(72/162) · xhdpi(96/216) · xxhdpi(144/324) · xxxhdpi(192/432) — legacy/adaptive
- **4 variants**: `ic_launcher`, `ic_launcher_round`, `ic_launcher_foreground`, `ic_launcher_monochrome`

**Gotcha**: Updating only xxxhdpi leaves stale icons on lower-density devices. Sanity-check by reading the actual git blame on the smallest size's last-changed commit.

**Reproducible pipeline (Python + PIL)**:
```python
from PIL import Image
src = Image.open("App_assets/1. App Icon_rev2.png").convert("RGBA")
W, H = src.size
S = max(W, H)
square = Image.new("RGBA", (S, S), (183, 23, 32, 255))  # EmergencyRed
square.paste(src, ((S-W)//2, (S-H)//2), src)
LEGACY = {"mdpi":48, "hdpi":72, "xhdpi":96, "xxhdpi":144, "xxxhdpi":192}
ADAPTIVE = {"mdpi":108, "hdpi":162, "xhdpi":216, "xxhdpi":324, "xxxhdpi":432}
# ... LANCZOS resize, save 20 files
```

The `mipmap-anydpi-v26/ic_launcher{,_round}.xml` and `ic_launcher_background.xml` stay untouched.

---

## 3. adb install version code downgrade (debug over release)

**Symptom**: `INSTALL_FAILED_VERSION_DOWNGRADE`. Release APK with versionCode=1610 installed; debug APK has versionCode=1.

**Fix**: `adb install -r -d <apk>` — `-d` flag allows downgrade. Preserves user data.

---

## 4. GitHub default branch rename (rename-then-delete pattern)

GitHub refuses to delete the default branch. To replace `Eject_Button_app` with `main`:

```bash
git branch main Eject_Button_app          # 1. create main locally
git push -u origin main                    # 2. push to origin
gh repo edit OWNER/REPO --default-branch main  # 3. flip default on GitHub
git push origin --delete Eject_Button_app  # 4. now safe to delete
git branch -D Eject_Button_app             # 5. delete locally
git fetch --prune                           # 6. clean refs
```

---

## 5. Git workflows on Windows + OneDrive folders

**Problem**: Workspace bash (Linux sandbox) cannot unlink `.git/index.lock` on Windows filesystem mounts → "Operation not permitted" warnings cascade.

**Solution**: Run all git commands from Windows PowerShell. `mcp__Windows-MCP__PowerShell` with `cd 'E:\Eject Button'; git ...`.

**Bonus**: PowerShell returns Status Code 1 even when git succeeds (because git uses stderr for normal progress output). Don't trust the status code — parse the output.

---

## 6. Play Console "관리형 게시" (managed publishing) workflow

**Mental model**: With managed publishing enabled, changes you save in the console go to a "변경사항 게시 준비됨" (changes ready to publish) queue. They are NOT live until:
1. You click "변경사항 X개 게시" (publish X changes)
2. Google reviews and approves
3. You manually publish the approved batch

**Implication**: It's safe to edit and "임시보관함에 저장" (save to draft) — nothing goes live. The risk is in clicking the "publish" button at step 1.

**Production track requirements**:
- ≥12 testers in closed test ✓
- ≥14 days of closed testing ✓
- Then "프로덕션 액세스 신청" (production access application) — answers some compliance questions, gates production publishing

---

## 7. AdMob secrets pattern (textbook)

`secrets.properties` (gitignored) holds ad unit IDs. `build.gradle.kts` reads via `secretsProps.getProperty(...)`. For release builds, it `error()`s if missing — refusing to ship test IDs to production. Debug builds fall back to AdMob's official test IDs.

```kotlin
buildConfigField("String", "ADMOB_NATIVE_ID",
    "\"${secretsProps.getProperty("ADMOB_NATIVE_ID")
        ?: if (isReleaseTask) error("ADMOB_NATIVE_ID missing - release refuses test fallback")
           else "ca-app-pub-3940256099942544/2247696110"}\"")
```

This pattern catches the classic "shipped test ad ID to production" bug at build time.

---

## 8. i18n wit preservation — onomatopoeia + role metaphors

For Eject Button, the Korean voice signature is:
- **Onomatopoeia**: 삐뽀삐뽀 (siren)
- **Role**: 본부 무전사 (HQ radio operator briefing a pilot)
- **Tone**: warm + military shorthand + question-driven

Cross-language equivalents that preserve the signature:
| Locale | Siren | HQ |
|---|---|---|
| ko | 삐뽀삐뽀 | 본부 |
| en | Beep beep | HQ |
| zh-CN | 嘀嘀！ | 总部 |
| zh-TW | 嘀嘀！ | 總部 |
| ja | ピーポー | 本部 |
| es | ¡Bip bip! | cuartel |
| hi | बीप बीप | मुख्यालय |

Emoji prefix consistency (📖/⏱/⚠/●) across all locales matters — diff individual entries when reviewing.
