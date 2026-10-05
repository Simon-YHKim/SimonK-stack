# Install — simon-stack

이 레포는 Claude Code 를 위한 통합 skill 스택(Gstack + simon-stack + Superpowers 철학)이다.

## 표준 갱신 경로 — `update-local.ps1` (Windows, 머지 직후마다)

main에 머지가 끝날 때마다 이 명령 하나로 이 PC의 사용자 홈 설치를 main에 맞춘다. 기본은 미리보기라서 `git fetch` 말고는 아무것도 쓰지 않는다. `-Apply`를 붙여야 설치한다. PowerShell 7(`pwsh`)이 필요하다.

```powershell
# 미리보기: 할 일을 JSON 보고서 하나로 보여 준다
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1
# 설치
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1 -Apply
```

> 이 경로는 사용자 홈에 flat으로 설치한다. 같은 PC에서 다섯 플러그인을 함께 켜지 않는다. 2026-10-05 세션 실측에서 스킬이 두 벌(563개)로 보이고 설명이 3만 자를 넘어 목록이 잘렸다. 플러그인으로 쓰는 PC는 README 3절의 마켓플레이스 설치를 따른다.

순서:
1. `git fetch origin` 후 main sha를 정한다.
2. `~/.claude/skills/vibe` 정션 대상에서 설치된 후보를 찾고, 그 영수증의 `main`을 읽는다.
3. 이미 최신이면 `"status": "current"`로 끝낸다(종료코드 0). sha만 비교하지 않는다. 다음 중 하나면 최신이다.
   - 같은 커밋이다.
   - 후보 입력에 변경이 없다. 입력은 `skills-src`·`.claude/skills`·`distribution`·`LICENSE`·`NOTICE`와 빌드 스크립트 4개다.
   - 정션이 가리키지 않는 스킬만 바뀌었고, 정션 8개의 설치 바이트가 main blob과 같다.
4. 빌드가 필요하면 여유 메모리부터 본다. 기본 3 GB보다 적으면 `LOW_MEMORY`로 멈춘다.
5. 같은 main으로 만든 후보(영수증 `main` 일치)가 있으면 영수증 4개를 다시 검증해 재사용한다. 없으면 `yyyyMMdd-vibe-<버전숫자>-<sha7>` 태그로 새로 빌드한다.
6. 정션 8개와 Codex `/vibe` config 줄을 바꾼다. 이전 태그는 정션에서 자동으로 읽는다. 열린 run, 진행 중 시도, halted 예산이 있으면 거부한다.
7. 실폴더 스킬(ai-debate·careful·freeze·guard·unfreeze)은 설치 바이트가 main과 다를 때만 바꾼다.
8. 검증한다: 설치본 vibe·vibe-bot `selftest.py`, Codex config 줄이 Claude vibe 정션 대상과 같은지, 버전. 하나라도 실패하면 이번 실행에서 바꾼 것을 모두 되돌린다.
9. JSON 보고서 하나를 출력한다. 종료코드 0은 preview·current·installed, 2는 차단 또는 되돌림, 3은 되돌림이 덜 된 상태다(보고서의 보관 경로를 확인한다).

| 매개변수 | 기본값 | 뜻 |
| --- | --- | --- |
| `-Apply` | 꺼짐 | 실제로 설치한다. 없으면 미리보기 |
| `-Ref` | `origin/main` | 설치할 커밋 |
| `-NoFetch` | 꺼짐 | `git fetch`를 건너뛴다 |
| `-RepoRoot` | 스크립트가 들어 있는 체크아웃 | 빌드용 워크트리를 만들 레포 |
| `-ReleasesDir` | 설치된 정션의 상위 폴더, 없으면 `E:\Coding Infra\Releases\SimonK-stack`, 그것도 없으면 필수 | 후보와 영수증이 있는 폴더 |
| `-PluginPins` | `ReleasesDir`에서 가장 최근의 유효한 폴더를 찾는다 | 플러그인 클론 5개(plugin-inputs.v1.json 커밋, 깨끗한 LF 작업 트리) |
| `-UserHome` / `-CodexHome` | 현재 사용자 홈 / `<홈>\.codex` | 설치 대상 |
| `-Tag` | `yyyyMMdd-vibe-<버전숫자>-<sha7>` | 새 후보 이름 |
| `-PhysicalSkills` | `ai-debate,careful,freeze,guard,unfreeze` | 실폴더로 관리하는 스킬 |
| `-MinFreeMemoryGB` | `3` | 빌드 전 최소 여유 메모리. 0이면 검사하지 않는다 |
| `-Selftest` | 꺼짐 | 바뀐 것이 없어도 selftest를 돌린다. 설치 뒤에는 항상 돈다 |

- 바꾸는 것은 전부 `~/.claude/flat-link-archive/` 아래로 옮겨 두고 지우지 않는다. 정션은 `vibe-<태그>/`(manifest, config 이전본), 실폴더는 `<스킬>-<yyMMdd-HHmm>-<sha7>/`에 남는다.
- 단계별 스크립트도 같은 폴더에 있고 기본은 모두 미리보기다: `build-candidate.ps1`, `install-junctions.ps1 -Tag <새 태그>`(`-OldTag`는 생략하면 자동), `install-physical.ps1`.
- agy는 정션을 따라가지 않아서 `~/.gemini/antigravity-cli/skills/<이름>` → `~/.claude/skills/<이름>` 심링크를 쓴다. 정션 대상만 바뀌므로 손댈 필요가 없고, 보고서의 `agy` 항목으로 상태만 확인한다. 정션을 새로 추가할 때만 같은 이름의 심링크를 만든다.
- 새 PC 첫 설치: 정션 자리가 비어 있으면 정션을 만들고, 실폴더가 있으면 보관한 뒤 정션을 만든다. Codex config에 `/vibe` 줄이 없으면 블록을 덧붙인다. 플러그인 핀 폴더는 레포에 없으니 `-PluginPins`로 넘긴다. 이 경로는 임시 홈 테스트로만 확인했다.
- 테스트: `python -B -m unittest discover -s scripts/tests -p test_windows_update_local.py`. 임시 홈만 쓴다.

## 2026-10-04 19:3x 후보 `20261004-vibe-2151-396aeae` — D-77·D-78 설치

- **D-77**(18:0x): 레포 `update-local.ps1`을 처음 실사용했다. main 77a28c2(vibe 2.15.0)로 후보 `20261004-vibe-2150-77a28c2`를 만들고 정션 8개를 전환했다. 사후 검증 단계가 하네스 메모리 회수로 끊겨, selftest(188/0·97/0)를 수동으로 돌렸고 다른 세션도 따로 확인했다.
- **D-78**(19:3x): main 396aeae(#120~#122)로 설치했다. 단계별로 포그라운드에서 실행했다.
  - 순서: `build-candidate.ps1 -Apply` → `install-junctions.ps1 -OldTag 20261004-vibe-2150-77a28c2 -Apply` → `install-physical.ps1 -Skills ai-debate,careful,freeze,guard -Apply`
  - 이전본: `~/.claude/flat-link-archive/vibe-20261004-vibe-2151-396aeae/`, `*-261004-d78/`
  - 결과: `update-local.ps1 -Selftest` 미리보기에서 `status: current`, problems 0.

## 2026-10-04 14:3x `/vibe` 2.14.2 · `freeze` 0.2.2 — D-71 설치

main `f6ec9c5`에서 조립한 후보를 설치했다. 반영된 PR은 셋이다.
- #114: 레지스트리 갱신(만료 2026-10-11 13:05 KST)
- #115: D-67 canary 반영(`pending-transport-and-certificate`)
- #116: 안전 런타임 20초 예산, Codex leaf deny 통과

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `0188255437422ff2b80014266311ac424d706f3a7e3bbcc016e2c7d095d0637f` (137스킬) |
| `candidate-safety` | `0ca1b08b231c801fffc3b4463d0e253827e3f1910d2427d9157990b7e10634f4` (182스킬) |
| `codex-overlay-safety` | `2b61437b2b05ef685add3727f3d2e8d1abb90e54ae755148ecd40f3acaf15f8c` |
| `codex-subset-safety` | `3a90ae709e077792d6e53f8fe0a942b34203ffc0ea5f2cb8ce05a23343c731a1` (177스킬) |

- 후보는 `E:/Coding Infra/Releases/SimonK-stack/20261004-vibe-2142-candidate/`이고 영수증 파일은 `20261004-vibe-2142-receipts.json`이다.
- 정션 8개와 Codex config 줄을 바꿨다. 되돌리려면 `~/.claude/flat-link-archive/vibe-20261004-vibe-2142/`를 쓴다.
- 실폴더 `freeze` 0.2.2를 main blob에서 복사했다(mismatch 0). 이전본은 `~/.claude/flat-link-archive/freeze-261004-d71/`에 있다. careful·guard·unfreeze는 바뀌지 않았다.
- 검증 결과:
  - 설치본 selftest: vibe 188/0, vibe-bot 97/0
  - 레지스트리 `checked_at` 2026-10-04T13:05:20+09:00
  - 설치 전에 열린 run은 없었다.

## 2026-10-04 04:2x `/vibe` 2.14.0 · `vibe-bot` 0.9.6 · `careful` 0.2.3 · `freeze`·`guard` 0.2.1 — D-70 설치

main `4c7a152`에서 조립한 후보를 설치했다. 반영된 PR: #109 vibe-bot G6 메뉴 범위, #110 Orca 현행 레인(D-67), #111 investigate 비설치(D-68), #112 안전 런타임 deny 통과(D-62 후속 5).

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `54aafc2a18d0211cae0478354a282c230658bd4e1c5c2aad8d8e7336d8bd6626` (137스킬) |
| `candidate-safety` | `78af5d308fca7ea2f45c1cac8851ad75b2e7163201c7628b6a0db4aa42b6b43e` (182스킬) |
| `codex-overlay-safety` | `ee79ae52bb0d7bf0542b8fb7fe3d81a3b7705830802903a3cded720bd17323d3` |
| `codex-subset-safety` | `9e9c4a71452ebc531a30d23912031b459365cc7414321060b13f2644352ad89c` (177스킬) |

- 후보: `E:/Coding Infra/Releases/SimonK-stack/20261004-vibe-2140-candidate/`
  - 영수증 파일: `20261004-vibe-2140-receipts.json`
  - 정션 8개와 Codex config 줄을 전환했다. 되돌리기: `~/.claude/flat-link-archive/vibe-20261004-vibe-2140/`
- 실폴더: `careful` 0.2.3과 `freeze`·`guard` 0.2.1을 main blob에서 복사했다(mismatch 0).
  - 이전본: `~/.claude/flat-link-archive/{careful,freeze,guard}-261004-d70/`
  - `unfreeze` 0.2.0은 그대로 뒀다.
- 설치 전에 열린 vibe run 2건(D-60·D-64 Grok Bot, 0원)을 `run_state.py complete`로 닫았다. 설치 스크립트는 열린 run, 진행 중 시도, halted 상태가 있을 때만 거부한다.
- 검증:
  - 설치본 selftest: vibe 188/0, vibe-bot 97/0
  - careful 훅 스모크: Bash HIGH deny, 일반 명령 allow, PowerShell HIGH deny
  - 훅 명령 자체는 바뀌지 않아서 새 세션 종단 시험은 생략했다.
- investigate: 홈 `~/.claude/skills/investigate`는 gstack 1.91.9 사본 그대로다(D-68). SimonK 소스(`skills-src/investigate/.simonk-no-install`)는 설치 대상이 아니다.

## 2026-10-04 01:5x `ai-debate` 0.2.5 — 결정 3단(D-65·D-66)

- PR #107(main `8afa150`). 홈 `~/.claude/skills/ai-debate` 물리 사본을 main blob에서 교체(7/7 일치), 설치본 테스트 통과. 이전 0.2.4 → `~/.claude/flat-link-archive/ai-debate-0.2.4-261004/`. Codex는 `~/.agents/skills/ai-debate` 심링크, Grok·agy는 `~/.claude/skills` 경로로 같은 폴더를 읽는다.
- 허브 D-66을 PROTOCOL §35.8 1단(오케스트레이터 단독)으로 기록한 첫 사례다.

## 2026-10-04 00:5x 안전 훅·vibe-bot 0.9.5 — D-60·D-62 설치, 위젯 D-63 재설치

main `edd9864`(PR #101 vibe-bot Relay active, #103 freeze·guard·unfreeze 0.2.0, #104 careful 0.2.2)에서 조립한 후보를 설치했다.

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `d98daaf701b0c42e8b61c2a4166f06a3facc87adf3697b1141e3412a9ae1b513` (137스킬) |
| `candidate-safety` | `8e49a803c6e31cd4bdb9844d1f52fc1de9234d2eb70ed395b2176ba6b13ae6ac` (182스킬) |
| `codex-overlay-safety` | `50ebaab3a477704ec3725841b72334f3d980d8273a3872444e0f4b9a5a036e07` |
| `codex-subset-safety` | `d6d26538bf07d12e6620c69db1c370d759cb0e78ffdadde4b8af59b0fb37c7cf` (177스킬) |

- 후보 `E:/Coding Infra/Releases/SimonK-stack/20261004-vibe-21310b-candidate/`, 영수증 파일 `20261004-vibe-21310b-receipts.json`. 정션 8개 + Codex config 줄 전환, 되돌리기 `~/.claude/flat-link-archive/vibe-20261004-vibe-21310b/`.
- 실폴더: `careful` 0.2.2, `freeze`·`guard`·`unfreeze` 0.2.0을 main blob에서 복사(전부 일치). 이전본 `~/.claude/flat-link-archive/{careful,freeze,guard,unfreeze}-261004/`(freeze·guard·unfreeze 이전본은 gstack 1.91.9 사본).
- 검증: 설치본 selftest 180/0. 새 대화형 Claude Code 세션(Orca 터미널, `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`)에서 종단 6/6 — Bash·PowerShell force-push(로컬 bare 원격) deny, PS 정상 명령 통과, freeze 경계 밖 Write deny·안 허용, unfreeze 후 허용, 원격 ref 불변.
- AI Usage Widget(D-61·D-63): 데이터 백업 `~/.claude/flat-link-archive/aiuw-backup-261003/`(base + incr-261004-003827, manifest 해시). fb5c9cf로 임시 재설치 후 `094da97`(PR #105 경고 수정) 고정 소스로 최종 재설치, app.asar `01115E890CEA…`, 계정·설정·인증 파일 해시 불변. 설치 스크립트는 반드시 `-Source <고정 워크트리>`(기본 체크아웃은 크게 뒤처짐).

## 2026-10-03 22:4x `/vibe` 2.13.1 · `ai-debate` 0.2.4 · `careful` 0.2.0 — D-59 설치

D-59(4벤더 토론 `dbt-261003-221019`, full, 블라인드 심판 Gemini 조건부 ALL · 확신도 85, 비준 3/3 ACCEPT, Grok 결석)에 따라
main `baafc70`(PR #96·#98·#97·#99)에서 조립한 후보를 설치했다.

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `fc5ed5ab35c2078314d39a4b6891280b124f7ff096fa3026a9ad1e3e34e694a4` (137스킬·435파일) |
| `candidate-safety` | `29eadd68c83af12b56074c5350a4696a1f499f221284880084fad2b138650edd` (5플러그인·182스킬·764파일) |
| `codex-overlay-safety` | `00dc17fb68e13fc94e3db70addd6948f83fe64cad9f706024229cbcd65102a84` |
| `codex-subset-safety` | `f9e24858af76be1d7589f7a24163178173d6850c7b8d822eaeadf41f07ba6acd` (177스킬, 안전 계열 5개 제외) |

- 후보: `E:/Coding Infra/Releases/SimonK-stack/20261003-vibe-21310-candidate/`(빌드 소스 = 깨끗한 detached 워크트리 `20261003-vibe-21310-src`, 플러그인 입력 `20261001-vibe-21241-candidate/plugin-pins-lf`).
- 정션 8개: Claude `vibe`·`vibe-bot`·`model-router`·`simonk`·`multi-terminal-dispatcher`·`qa`, Codex `vibe`·`vibe-bot`. 전환 전 토폴로지·트리 digest 확인, 이동 보관 후 정션 생성, 새 digest 재확인, 실패 시 자동 롤백. `~/.codex/config.toml`의 `.agents` /vibe 비활성 줄을 새 후보 경로로 교체(야간 QA 설치 뒤 옛 2.12.43 경로에 남아 있었음).
- 되돌리기: `~/.claude/flat-link-archive/vibe-21310-261003/`(manifest.json, 이전 정션 8개, `codex-config.toml.before`, `gemini-skills.json.before`).
- agy: `~/.claude/skills/qa`가 정션이 된 뒤 agy가 qa를 못 봤다 → `~/.gemini/antigravity-cli/skills/qa` 심볼릭 링크 + `skills.json` 제외 목록에 `qa`. 4개 CLI 182/182 동일.
- 검증: 설치본 selftest 180/0, 레지스트리 `checked_at` 2026-10-03T21:42:01+09:00(만료 10-10 21:42 KST).
- `ai-debate` 0.2.4: 물리 사본 교체(main blob 7/7 일치, 설치본 테스트 110/110). 이전 0.2.3 → `~/.claude/flat-link-archive/ai-debate-0.2.3-261003/`.
- `careful` 0.2.0: gstack 1.91.9 사본 → `~/.claude/flat-link-archive/careful-gstack-1.91.9-261003/`, main 6파일 복사(일치). 설치 직후 새 대화형 Claude Code 세션(bypassPermissions)에서 로컬 bare 원격으로 `git push --force origin main` → `[careful][HIGH] Force-push to the default branch (main) is blocked while /careful is active.` deny, 원격 ref 불변, `echo` 통과. guard·freeze·unfreeze·investigate는 아직 gstack 사본.

## 2026-10-03 `ai-debate` 0.2.3 — Grok 좌석 실시간 billing 조회

D-57(4벤더 토론 `dbt-261003-210004`, quick, 블라인드 심판 Gemini 조건부 MERGE_INSTALL · 확신도 92)에 따라
[PR #93](https://github.com/Simon-YHKim/SimonK-stack/pull/93)을 머지(`5e4cae8`)하고 홈 사본을 교체했다.

- 교체: `~/.claude/skills/ai-debate`(물리 폴더). main blob에서 7개 파일을 그대로 꺼내 `git hash-object`로 7/7 일치 확인. 설치본 테스트 104/104.
- 되돌리기: 이전 0.2.2는 `~/.claude/flat-link-archive/ai-debate-0.2.2-261003/`(7개 파일)으로 옮겨 두었다. 되돌릴 때는 현재 폴더를 다른 보관 폴더로 옮긴 뒤 이 폴더를 원래 자리로 옮긴다.
- 4개 CLI: Codex는 `~/.agents/skills/ai-debate` 심링크, Grok은 `~/.claude/skills` 호환 경로, agy는 `skills.json`의 `~/.claude/skills` 항목으로 같은 폴더를 읽는다(경로 변경 없음).
- 같은 시점 홈의 `/vibe`는 **2.13.0**이다. 이 버전은 10-03 03:43 야간 QA 세션이 `feat/qa-evidence-261003` 브랜치 후보(`E:/Coding Infra/Releases/SimonK-stack/20261003-vibe-2130-qa-final`)로 `vibe` 정션 2개와 `qa`만 바꾼 것이다(되돌리기 `~/.claude/flat-link-archive/vibe-qa-261003-2130/`). main에는 아직 2.12.43이 있다. 나머지 Core 5개 정션은 2.12.43 후보에 그대로 있다.

## 2026-10-03 `/vibe` 2.13.0 · `/qa` 2.1.0 — QA 완료 게이트 설치

Simon의 `/vibe` 연동·최종 개선 요청에 따라 `feat/qa-evidence-261003`의 소스
`cf139c3837d071e7113cf837d6d03b935f4332f6`를 패키징하고 아래 세 경로만 전환했다.
기능 소스는 feature 브랜치에 push됐으며 main 병합·운영 배포·자동 PR은 하지 않았다.

| 설치 경로 | 대상 |
| --- | --- |
| `~/.claude/skills/vibe` | 아래 후보 `candidate-safety/plugins/SimonKCore/skills/vibe` (2.13.0) |
| `~/.codex/skills/vibe` | 아래 후보 `codex-subset-safety/plugins/SimonKCore/skills/vibe` (2.13.0) |
| `~/.claude/skills/qa` | 아래 후보 `candidate-safety/plugins/SimonKStack/skills/qa` (2.1.0) |

`.agents/skills/{vibe,qa}`는 기존 `.claude` 연결을 통해 새 버전을 읽는다.
다른 Core 링크·ai-debate·호스트 설정·자격증명·gstack 홈은 변경하지 않았다.
따라서 모든 Core 링크가 같은 후보 루트를 가리킨다고 가정하면 안 된다.

후보: `E:/Coding Infra/Releases/SimonK-stack/20261003-vibe-2130-qa-final/`.
이전 정션 두 개와 물리 QA 폴더, 파일 해시·전환 기록은
`~/.claude/flat-link-archive/vibe-qa-261003-2130/manifest.json`과 같은 폴더에 보존했다.
복구 시 새 연결도 별도 보존한 뒤 해당 이름의 백업을 원래 경로로 이동한다.
현재 연결을 통해 재귀 삭제하지 않는다.

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `4d7c26c9e74730d13d884649a95fb404d5b16849d356a7e6ffe947452eb49bfb` |
| `candidate-safety` | `dc14805d096da2edc243d1c0e44b76dca87b9d305d8c2ab728ab7b06e6debfe5` |
| `codex-overlay-safety` | `a4d114ac0e4bcd9a613c3ad02ca0d3da06db789d39ca63abaec6366fd8b12af9` |
| `codex-subset-safety` | `dda20051135eaee70a419f0b01c80f7acdc8f4bd016b888023c9946de797aa4f` |

네 영수증 재검증 PASS. 실제 Codex 설치 경로 410 tests, Claude 설치 경로
run-state 67 tests, `.agents` QA 경로 33 tests PASS. 소스 selftest 180,
Skill-Gen 통합 24, 전체 141 skill 품질 검사도 PASS. 이는 오프라인 계약/경로 검증이며
모델 생성·비용·제품 E2E·전체 플러그인 설치 준비를 증명하지 않는다.

완료 게이트 사용법은 [QA completion gate](../skills-src/vibe/references/orchestration.md#qa-completion-gate).
열린 변경/coding/qa run은 `bind-qa`가 없으면 완료되지 않는다. 검증할 빌드와 계약
해시를 독립적으로 고정하고, 명시 QA 경로를 사용한다. 이 PC의 공용 QA 경로는
`C:/Users/202502/.agents/skills/qa`다. 고위험 검토·독립 벤더 리뷰·배포 권한은 별도다.

토론은 앞선 사용자 정족수 예외 승인 아래 Google advisory로 검토했다.
최종 재검토 `dbt-261003-vibeqa-check`는 즉시 차단 결함 없음으로 판단했고,
핀으로 제한한 동적 로딩의 신뢰 경계는 문서화했다. 정식 4벤더 합의로 기록하지 않는다.
## 2026-10-02 `/vibe` 2.12.43 · `ai-debate` 0.2.2 — 4개 CLI 동일 설치

D-55(4벤더 토론 `dbt-261002-020448`, 블라인드 심판 대안 4 · 확신도 92)에 따라 main `9e88140`에서
조립한 후보를 설치했다. ai-debate 0.2.2는 판정 조건인 오프라인 리플레이 게이트(4벤더 실기록,
18건 기대대로)를 통과한 뒤 교체했다.

| 패키지 | SHA-256 영수증 |
| --- | --- |
| `source` | `de193be5b2c1256ce9ecd5c2db926e98054174e740ae3be21c9093116b99fc2d` (137스킬·430파일) |
| `candidate-safety` | `24fe0d33e17094a6d275784d4eca12c554ba53522d62f0737473bd32b6adb7fb` (182스킬·759파일) |
| `codex-overlay-safety` | `87fea4e405f1f2e18baf0a25a1f6b60d8f729401403b2f18e6f2fde3eaa10c9d` |
| `codex-subset-safety` | `7fd63cc8e45cce9a0dc80ac9301a11815d00c95be7a47ba0e36fc81906060eee` |

후보: `E:/Coding Infra/Releases/SimonK-stack/20261002-vibe-21243-candidate/`. 매니페스트·되돌리기:
`~/.claude/flat-link-archive/vibe-24fe0d33e170/`(정션 7개, Codex config 사전 이미지, `ai-debate-0.2.1`).

4개 CLI가 같은 파일을 읽는 구조:

| CLI | 스킬 경로 | 비고 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills` | Core 7개는 후보 정션 |
| Codex | `~/.codex/skills` + `~/.agents/skills` | `~/.agents`는 대부분 `~/.claude/skills` 심링크, 플러그인 경유분은 `simonk-core:` 접두어 |
| Grok CLI | `~/.grok/skills` + `~/.claude/skills` 호환 | |
| agy 1.2.14 | `~/.gemini/antigravity-cli/skills` + `~/.gemini/config/skills.json` | agy는 정션을 따라가지 않고 `~/`를 거부한다. `skills.json`에 절대 경로 `C:\Users\202502\.claude\skills`(hyperframes 11개·정션 7개 제외)와 `~/.agents/skills`(Orca 2개)를 두고, Core 5개는 agy 폴더에 `~/.claude/skills/<이름>` 심볼릭 링크로 둔다. 확인 = 무턴 `agy -p "/skills" --output-format json` |

같은 날 `~/.claude/skills`의 SimonK 자체 스킬 31개를 main과 바이트 동일하게 동기화했다(이전 사본
`~/.claude/flat-link-archive/skills-261002-sync/`). gstack 원본으로 덮인 34개는 gstack-upgrade 관리 영역이라
그대로 두었다. 검증: 영수증 4/4, 런타임 probe 통과, 후보 경로 orchestrate 144·model_registry 36·
run_state 53, 사전검사 `different_skills=0`, selftest 180/180(Claude·Codex), agy가 Claude의 182개를
접두어·중복 없이 인식. 설치 직후 첫 영수증·사전검사가 rc 2를 내는 일시 현상이 두 번 재현됐고
재실행에서는 정상이다(스킬 목록 재로딩 시점으로 추정).

레지스트리 사실 유효기간은 2026-10-09 00:39 KST까지다. 그 전에 다시 확인해 갱신해야 한다
(예약 작업 `\SimonK-Vibe-RegistryRefresh-Reminder` 10-08 09:00).

## 2026-10-01 `/vibe` 2.12.42 · `ai-debate` 0.2.0 — 사용자 홈 설치 완료

Simon의 직접 지시("스킬 업데이트를 완료해줘")와 §35 4벤더 토론 D-53(PROVISIONAL 2/4,
블라인드 심판 조건부 GO, 비준 ACCEPT 2/2)에 따라 D-39/D-50의 사용자 홈 HOLD를 해제하고
평면 Core 링크만 전환했다. 네이티브 플러그인 등록과 133개 물리 폴더는 바꾸지 않았다.

후보는 main `bfee665`의 깨끗한 detached 워크트리에서 조립했다
(`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-21242-candidate/`,
플러그인 입력은 `20261001-vibe-21241-candidate/plugin-pins-lf`의 고정 커밋).

| 패키지 | SHA-256 영수증 | 범위 |
| --- | --- | --- |
| `source` | `fdf49700c59b415737c17daa1432707e886cf04bf8f89fbfa5e7ddeaa5d6d42c` | 137스킬·429파일 |
| `candidate-safety` | `9b4cf24efd9feb495018717128f45dd40f4c8a1c9e1c7e38a57634cee482138c` | Claude 5플러그인·182스킬·758파일 |
| `codex-overlay-safety` | `a8afac169e53d9eca714d3e4a1a63d1a98dfd7ca28f118137e5ba282ad23f38a` | Codex 호환 오버레이 |
| `codex-subset-safety` | `80659a1ca7be652c975914fa0ee9a9441061c79f010f67194aeed7b2f636582f` | Codex 안전 부분집합 177스킬 |

설치 단계(같은 날 두 번, 같은 방식): 2.12.24 → 2.12.41 → 2.12.42.

1. 전환 직전 `%LOCALAPPDATA%/SimonK/vibe/runs.sqlite3` 부재로 진행 중 preparation·바인딩된
   Orca 실행 0건을 확인했다.
2. Claude 정션 5개(`model-router`, `multi-terminal-dispatcher`, `simonk`, `vibe`, `vibe-bot`)와
   Codex 정션 2개(`vibe`, `vibe-bot`)를 같은 볼륨에서 `<host>/flat-link-archive/<run>/<name>`으로
   이동 보관하고 새 후보를 가리키는 정션을 만들었다. 기존 대상 폴더는 삭제하지 않았다.
3. `~/.codex/config.toml`의 `/vibe` 중복 제거 `[[skills.config]]` 경로 한 줄만 새 후보로 바꿨다.
4. `~/.claude/skills/ai-debate` 물리 폴더(0.1.0)를 보관 이동하고 후보의 0.2.0 사본으로 교체했다.
   `~/.agents/skills/ai-debate` 심링크를 거쳐 Codex도 0.2.0을 읽는다.

매니페스트와 사전 이미지는 `~/.claude/flat-link-archive/vibe-09ff36f49f15/`(2.12.41)과
`~/.claude/flat-link-archive/vibe-9b4cf24efd9f/`(2.12.42)에 있다. 되돌리기는 매니페스트의 보관
링크를 원위치로 이동하고 config 한 줄을 역치환한 뒤, `ai-debate-0.1.0` 보관 폴더를 복원한다.

검증: 영수증 4/4(빌드 직후·후보 경로 테스트 뒤·설치 뒤), 런타임 probe 통과, 후보 경로
`test_orchestrate` 138·`test_run_state` 53·ai-debate 77 OK, 호스트 사전검사
`different_skills=0`·`issues=[]`, 설치 경로 selftest 180/180(Claude·Codex), 표 동기 OK,
설치본 `run_state.py gstack-env` 스모크(telemetry off·update_check false, DB 미생성), 개인
`~/.gstack` 불변. 사전검사는 간헐적으로 7개 링크 전부를 `LINK_TARGET_MISMATCH`로 오판했고
(직접 readlink 492회는 동일), 2.12.42 전환 직후 한 번 영수증·사전검사가 rc 2를 냈으나
재실행에서 재현되지 않았다. 판정은 직접 readlink와 영수증을 함께 본다.

`installation_ready`·`host_compatibility_verified`·`billing_verified` 필드는 패키지 수준 값이라
여전히 false다. 이 설치는 실사용 자동 선택·구독 청구·이미지·Grok Bot 경로를 증명하지 않는다.
Codex·Grok 좌석은 쿼터 소진으로 D-53에 결석했으며 복귀 후 `ai-debate` catch-up이 남아 있다.
이미 열린 Claude·Codex 세션은 이전 스킬 목록을 캐시하므로 새 세션에서 반영된다. 로컬 기본 체크아웃
(`E:/Coding Infra/Harrness Eng/SimonK-stack`, 오래된 main)을 프로젝트로 열면 hold 검사가 없는
구 SessionStart 훅이 스킬을 실폴더로 덮을 수 있다.

## 2026-10-01 `/vibe` 2.12.41 설명 축약 대응 후보 — 기본 설치 보류

소스 커밋 `9a49365`에서 이전 후보와 별도의
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-21241-quality-candidate/`를 조립했다.
고정한 다섯 원본 플러그인 커밋은 `distribution/plugin-inputs.v1.json`과 같다.
원본 저장소와 기존 2.12.40 후보·격리 프로필은 변경하지 않았다.

| 패키지 | SHA-256 영수증 | 범위 |
| --- | --- | --- |
| `source` | `8beeada95c0a0c7a7581701bc394d65bfeffa6e2fce7cfd7975479ced7b3fb4a` | 137스킬·424파일 |
| `candidate-safety` | `09ff36f49f15a2ac92426e889eaf7b4fb2b6d9ffe043b2b8a0668f541e149782` | Claude 5플러그인·182스킬·753파일 |
| `codex-overlay-safety` | `b852e17df14f14c027a5d3059ba7ec299e1b8800b44f294b6633a5dde2896bbc` | Codex 호환 오버레이 |
| `codex-subset-safety` | `b6930526b3118e53cf890b934a47da6ceb0e818fd897a544e5bd4683f29b6970` | Codex 안전 부분집합 177스킬 |

네 영수증을 각 검증기로 다시 확인했다. `/vibe` 오프라인 라우팅 검사
131/131, 자체검사 180/180, 후보 런타임 probe 4/4 및 스킬 validator
0 error/0 warning이 통과했다. 이전 2.12.40 후보와의 버전 정규화 비교에서
실제 스킬 파일 변경은 Core `skills/vibe/SKILL.md`와 회귀 테스트
`skills/vibe/scripts/test_orchestrate.py` 두 개뿐이었다. 현재 PC의
별도 Codex 무인증 프로필에 앞선 2.12.41 후보 플러그인 5개를 설치해 모델 미호출
`debug prompt-input`을 검사한 결과 181개 스킬 중 namespaced
`simonk-core:vibe`·`simonk-core:vibe-bot`가
각각 한 번 노출됐고, 축약된 `/vibe` 설명은
`Use when "/vibe" routes SimonKStack work acros`로 시작했다.

이것은 설명 발견성·패키지 바이트 검증이지 자연어 자동 선택, Claude 새 후보의
실제 명령 수락, 모델/effort 실행, 구독 청구, 이미지 생성 또는 Grok Bot 전달의
증거가 아니다. 기본 사용자 홈 `/vibe`는 여전히 2.12.24이며 D-39/D-50
설치 보류와 `installation_ready=false`를 유지한다. 이미지·모델·Bot 실호출,
결제·자동충전 설정 변경 및 추가 과금은 없었다.

## 2026-10-01 `/vibe` 2.12.40 정확한 main 격리 후보 — 설치 보류

[PR #80](https://github.com/Simon-YHKim/SimonK-stack/pull/80)의 일반 머지
`102b48740f68f446dca6fab4ecc97d1bd96d149c`에서 별도 격리 소스
worktree를 만들고, 고정된 5개 플러그인 입력으로 새 후보를 조립했다.
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-main-102b487-candidate/`
아래에 있으며 이전 후보와 사용자 프로필은 보존했다.

| 패키지 | SHA-256 영수증 | 범위 |
| --- | --- | --- |
| `source` | `85e9fd2767cdf83d7ee5e8b217ed813e4089322f64d94736c747b8c3ad84d815` | 137스킬·424파일 |
| `candidate-safety` | `3d5661efb3126656049a6111497f4ff5893e2a7e88a1d7119ba9f3743f850310` | Claude 5플러그인·182스킬·753파일 |
| `codex-overlay-safety` | `11ae3f533f34dfeaa38355be24f0f573f60d888ba2a59125d14e24451888f09a` | Codex 호환 오버레이 |
| `codex-subset-safety` | `a63f24560927c6950f9fa2669a03600e5e617a9dd6b15d7164d8afc41a9ff603` | Codex 안전 부분집합 177스킬 |

이 영수증은 복사된 후보 바이트와 출처 연결을 확인하지만 Git 커밋 자체의
독립 서명은 아니다. 빌드 전 작업트리는 위 `main` 커밋에서 깨끗했고,
소스 매니페스트의 424개 `source_path`는 현재 체크아웃과 해시가 일치한다.

네 패키지의 별도 바이트 재검증과 subset 출처 검증, 오프라인 `/vibe`
selftest·runtime·prepare·table-sync 4단계가 통과했다. 실제 사용자 프로필의
읽기 전용 사전검사는 핵심 링크 8/8과 후보 바이트 4/4를 확인했으나 전체
flat 본문 일치는 Claude 4/182·Codex 4/177이다. 기존 Claude 물리 폴더에는
후보에 없는 보조 파일 224개가 있어 일괄 교체하면 자산 손실 위험이 있다.
현재 네이티브 플러그인 등록은 Claude·Codex 모두 후보 5개 중 0개다.

`installation_ready=false`, `host_compatibility_verified=false`,
`runtime_closure_verified=false`, `billing_verified=false`다. 이 후보는
Claude/Codex 실제 선택·모델/effort·구독 청구, 이미지 생성, Grok Bot 전달,
Antigravity/Grok CLI 실행을 입증하지 않는다. D-39의 사용자 홈 설치 NO-GO와
소스 전용 release/SessionStart hold, marketplace pin을 유지한다. 사용자 flat
정션·플러그인 등록·결제 설정은 변경하지 않았다.

## 2026-10-01 `/vibe` 2.12.37 동시 Orca 기준선 갱신 보호

Claude·Codex가 같은 외부 기준선을 동시에 보고하거나 확인할 때 2.12.36은
마지막 쓰기가 앞선 `pending`을 지울 수 있었다. 2.12.37은 사용자 상태 폴더의
지속되는 `.lock` 파일에 OS 잠금을 걸어 목록 조회·읽기·병합·교체와
기준선 이전·확인 처리를 직렬화한다. 긴 조회 중 다른 호출이 5초 안에
잠금을 얻지 못하면 실패하며 재시도 시 기존 요청의 결과를 먼저 확인한다.
잠금 획득 실패는 `미확인`과 비정상 종료로 처리하며 기존 JSON을 수정하지 않는다.
파일 자체는 완전히 쓰고 fsync한 뒤 원자적으로 교체한다.

전체 보고의 `pending_digest`는 검토한 현재 스킬 목록과 미확인 변경 묶음의
고유 세대를 가리킨다. `seen_count`만 늘어난 동일 변경은 같은 토큰을 유지하지만,
확인 후 새 묶음은 목록이 같은 초에 원래대로 돌아와도 새 토큰을 받는다.
기존 pending에 세대가 없으면 다음 보고가 발급한다. 스킬 문서를 검토한 다음 보고에 표시된
정확한 토큰으로만 확인 처리한다. 토큰이 없거나 오래됐으면 종료 코드가 0이
아니며, 새 보고를 확인해야 한다.

```powershell
python -B skills-src/vibe/scripts/check_tooling.py --ack-skills <보고의-pending_digest>
```

이 수정은 소스 단계다. 아래 2.12.36 격리 후보는 이 잠금·CAS 코드를 담지
않으므로 설치 대상으로 승격하지 않는다. 이 문서의 다른 설치·호스트·청구
게이트도 그대로 적용된다. `--ack-skills`는 로컬 상태를 변경하므로 실제
사용자 기준선에서는 변경을 직접 검토한 뒤에만 실행한다.

## 2026-10-01 `/vibe` 2.12.36 Orca 기준선 외부 저장 격리 후보

2.12.35 후보는 전체 툴링 보고 또는 `--ack-skills`가 후보의
`vibe/state/orca-skills.json`을 기록해 해시 영수증을 깨뜨린다. 따라서
2.12.35의 사용자 Core flat 링크 7개 승격은 D-41에서 보류했다.
2.12.36은 이 가변 파일을 Windows의
`%LOCALAPPDATA%/SimonKStack/vibe/orca-skills.json`(다른 OS는
`XDG_STATE_HOME` 또는 `~/.local/state/SimonKStack/vibe`)에 둔다.
패키지 내부 경로로 해석되거나 기존 JSON이 손상되면 새 기준선으로
조용히 덮지 않고 `미확인`으로 실패한다.

기존 설치본의 기준선은 읽기 전용으로 먼저 확인한다. 실제 사용자 PC에서
새 후보의 첫 전체 보고 전에, 확인된 기존 파일 경로를 다음 명령에 명시해
외부 상태로 한 번만 이전한다. 대상이 이미 있으면 덮어쓰지 않고 실패한다.
이전 파일은 먼저 임시 파일에 완전히 쓴 뒤 배타적으로 게시하므로 중간
쓰기 실패가 부분 대상 파일을 남기지 않는다.
`--local-codex`는 계속 Orca·npm 원격 조회와 상태 기록을 하지 않는다.

```powershell
python -B skills-src/vibe/scripts/check_tooling.py --migrate-snapshot '<확인된 기존 설치본>/state/orca-skills.json'
```

격리 후보 경로는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-external-state-v2-candidate/`다.
앞선 2.12.36 후보는 보존했지만 PR #74의 Ubuntu CI가 테스트의 OS별
상태 폴더 격리 누락을 검출해 사용하지 않는다. 새 후보의 소스 137스킬·
423파일 digest는 `393a690ea2b4f2ff1759cd23cee8ecf9d85c4b4a639f90a01f30eb5a260e8146`,
Claude 5플러그인·182스킬 `595c8bd928d2f043a5e443054eb34d193eb397478ce7b9b5cbb0b83f1259a15a`,
Codex 오버레이 `0a52d5bcacd6526401153e135e104f74a3ac55870d66f1dd4674863a31bb1f4f`,
Codex 안전 subset 177스킬 `49d66bd93f46b8b84eaba043ffbf516e2e6ca0da117fa245aad2f19519a66f9e`다.
네 영수증 모두 재검증됐고 현 HEAD의 `/vibe` 스크립트 테스트 338건·
자체 점검 180항목·WSL Ubuntu의 `test_check_tooling.py` 16건이 통과했다.
직전 HEAD의 저장소 테스트 427건(3건 skip)도 통과했으나 이번 수정 후
전체 저장소 테스트를 다시 실행했다고 주장하지 않는다. 후보 코드의
오프라인 Orca 보고→미확인 변경→확인 처리 후 Claude/Codex 영수증도
동일했다. 기존 Codex 설치본의 8스킬 기준선은 원본 SHA-256을 유지한 채
사용자 외부 상태로 동일 SHA-256으로 복사했다.
실제 프로필의 읽기 전용 사전검사는 8/8 링크·후보 바이트를 확인했고
문제 0건이었으나 네이티브 플러그인 등록 상태는 이번에 관측하지 않았다.

이 결과는 패키지 바이트와 오프라인 동작 증거이지 실제 사용자 프로필
선택·구독 청구·모델/Bot 실행 증명이 아니다. `installation_ready=false`,
`host_compatibility_verified=false`, `runtime_closure_verified=false`를 유지한다.
Claude·Codex가 같은 외부 기준선을 공유하므로 동시 보고/확인 처리의
잠금·CAS는 아직 없다. 동시 실행 중 변경 유실 가능성을 사용자 설치 승격 전
별도 테스트·보강한다.
사용자 링크 전환·`main` 머지·모델/이미지/Bot 실호출은 별도 판정이며,
추가 과금 $0 및 구독 포함 경로 한정은 그대로다.

## 2026-10-01 `/vibe` 2.12.35 과금 관측 정합성 최종 격리 후보

독립 검토에서 2.12.32 수집기가 비표준 Codex 한도 버킷을 조용히 버려
구매 크레딧을 숨길 수 있음이 재현됐다. 2.12.35는 비표준 ID·비객체 버킷·
비객체 버킷 모음을 `billing-shape-unknown`으로 거부한다. 중첩 금액의
`val`·`value`가 충돌하면 잔액을 알 수 없음으로 처리해 계획 및 최종 CLI
가드에서 차단한다. Grok의 외부·레거시 중첩 `onDemandEnabled`·
`on_demand_enabled`가 모순이어도 어느 쪽을 우선하지 않는다.

새 후보는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-billing-consistency-candidate/`에
있으며 이전 2.12.32~2.12.34 후보와 사용자 설치본을 보존했다.

| 산출물 | 검증된 전체 digest | 범위 |
|---|---|---|
| `source` | `97699b4d074b5fe09a9080dc2b7364c2c5fb68733a02381ad99a51ac855f28ce` | 137스킬·423파일 |
| `candidate-safety` | `1aa454151c48cbe64f7734479739e8d637d885200d10837580e4b03c8330109e` | Claude 5플러그인·182스킬 |
| `codex-overlay-safety` | `355db0e5c2a36f7a3ba39fc21c25b5287c2f54f44da5beaec61775b9620416b8` | Codex 호환 오버레이 |
| `codex-subset-safety` | `e3e366d488a8a9f0475dcb7f0e94aad500257e69f841598a1afcd495db05c698` | Codex 177스킬·출처 검증 |

네 영수증을 별도 재검증했고, 오프라인 probe 4/4, `/vibe` 단위 테스트
333건, 자체 점검 180항목, 전체 스킬 품질 141/141, 라우팅 표 동기화가
통과했다. 저장소 `runtime_collect.py`와 후보 소스의 SHA-256이
`0b7c31c05543e20e590124c5a2dbdcdf480375a7d655f4de200b3b80ae70cf95`로
일치한다. 실제 계정이나 모델을 호출한 테스트는 없다.

정확한 2.12.35 후보를 네트워크·클립보드·장치 리디렉션과 사용자 인증정보가
없는 별도 Windows Sandbox 두 곳에서 적재·복원했다. Claude Code 2.1.285는
5플러그인·182스킬·디버그 오류0, 고정 Codex CLI 0.155.0은 5플러그인
활성화가 통과했다. 양쪽 모두 이전 Claude5·Codex2 링크를 두 번 복원하고
시험 플러그인 최종0, 네트워크 어댑터0·모델 생성0이었다. 원시 결과는
`host-rehearsal/claude-output/integrated-result.json`(SHA-256
`e4fd8b902a6f0833128223dafc7e11e805db4ae8364da726ae6d539c90a77c71`)과
`host-rehearsal/codex-output/codex-integrated-result.json`(SHA-256
`d41fbfd3ffd05ff7ae809df18ce1c9ec3b4615d8c21afc050ca15ea467a7553b`)이다.
두 게스트는 종료됐다.

이 결과는 격리 호스트 적재·복원에 한정된다. 실제 사용자 홈 설치,
모델·effort 자동 선택 품질, 이미지 생성, Grok Bot 배달, Gstack 전체
외부 런타임 및 구독 청구는 검증하지 않았다. `installation_ready=false`,
`host_compatibility_verified=false`, `runtime_closure_verified=false`를 유지한다.
이후 독립 심판 D-38과 정확한 PR HEAD CI를 거쳐 #68·#69가 소스 전용으로
`main`에 머지됐다. 운영 Cloudflare Pages 자동 배포는 사용자가 허용했으나
설치·실호출 허가는 아니다. D-39는 실제 사용자 홈 전환을 계속 보류하고
오프라인 shadow 검증만 허용했다.

### 사용자 flat 링크 읽기 전용 사전검사

`scripts/vibe_host_preflight.py`는 후보와 현재 프로필에서 Claude Core 정션
5개, Codex 정션 2개, `.agents`의 `/vibe` 별칭 1개만 읽는다. 이전 후보 루트를
명시적으로 받아 각 직접 대상·링크 종류·`SKILL.md` 해시를 비교한다. 이어서
후보의 다섯 플러그인 스킬 루트와 각 호스트의 flat 스킬 루트를 기존
`/vibe` 메타데이터 스캐너로 대조한다. 어느 단계도 링크를 이동하거나 바꾸지 않는다.
Windows 정션은 Python 3.11에서도 지원하며 Windows CI가 해당 회귀 테스트를
실행한다. 출력 JSON에는 절대 프로필·후보 경로 대신 대상 일치 여부와 해시만 담는다.
실제 프로필에서 8/8 링크 구조가 일치했고, `/vibe`의 Claude·Codex 두
본문만 후보와 달랐다. 전체 SKILL.md 감사에서는 Claude 후보 182개 중
일치 4·변경 134·미설치 44, Codex 안전 부분집합 177개 중 일치 4·변경 128·
미설치 45다. 물리 폴더의 상대 파일명 차이도 읽기 전용으로 집계하지만,
파일 내용·필요성·출처, 플러그인 등록·실제 호스트 적재와 명령 우선순위,
모델·effort 선택, 계정 청구와 이미지·Bot 전달은 범위 밖이다.

```powershell
$vibeCandidate = 'E:\Coding Infra\Releases\SimonK-stack\20261001-vibe-pr69-billing-consistency-candidate'
$vibeCurrent = 'E:\Coding Infra\Releases\SimonK-stack\20261001-vibe-bot-gate-fix'
python -B scripts/vibe_host_preflight.py --candidate-root $vibeCandidate `
  --expected-current-root $vibeCurrent `
  --claude-root "$env:USERPROFILE\.claude" --codex-root "$env:USERPROFILE\.codex" `
  --agents-root "$env:USERPROFILE\.agents" `
  --source-digest 97699b4d074b5fe09a9080dc2b7364c2c5fb68733a02381ad99a51ac855f28ce `
  --claude-digest 1aa454151c48cbe64f7734479739e8d637d885200d10837580e4b03c8330109e `
  --overlay-digest 355db0e5c2a36f7a3ba39fc21c25b5287c2f54f44da5beaec61775b9620416b8 `
  --codex-digest e3e366d488a8a9f0475dcb7f0e94aad500257e69f841598a1afcd495db05c698
python -B -m unittest scripts.tests.test_vibe_host_preflight -v
```

네 digest는 위 배포 표의 **별도 고정값**이다. 하나라도 누락·불일치하면
호스트 스캔 전에 `CANDIDATE_VERIFICATION_FAILED`로 차단한다. 네 값이 모두
맞으면 기존 source·Claude bundle·Codex overlay·안전 부분집합 검증기로
파일 바이트와 출처 연결을 확인해 `candidate_bytes_verified=true`로 보고한다.
이는 SHA-256 고정 후보 확인이지 서명이나 실행 중 파일 불변성 증명이 아니다.
digest 인수를 생략한 종전 호출은 `candidate_verification.status=not_requested`와
`candidate_bytes_verified=false`로 남는다.

네이티브 플러그인 등록 상태도 보려면 같은 후보·프로필 인수에
`--native-json-stdin`을 추가하고 아래처럼 각 호스트의 현재 목록을 메모리에서
전달한다. 이 옵션은 `claude plugin list --json`의 배열과
`codex plugin list --json`의 `installed` 배열에서 후보 5개 플러그인의
정확한 `name@marketplace`·버전·활성 상태만 집계한다. 원본 목록·로컬
경로는 보고서에 출력하지 않는다.

```powershell
$claudePlugins = claude plugin list --json | ConvertFrom-Json -Depth 30
$codexPlugins = codex plugin list --json | ConvertFrom-Json -Depth 30
@{claude=$claudePlugins;codex=$codexPlugins} | ConvertTo-Json -Depth 30 -Compress |
  python -B scripts/vibe_host_preflight.py --candidate-root $vibeCandidate `
    --expected-current-root $vibeCurrent --claude-root "$env:USERPROFILE\.claude" `
    --codex-root "$env:USERPROFILE\.codex" --agents-root "$env:USERPROFILE\.agents" `
    --source-digest 97699b4d074b5fe09a9080dc2b7364c2c5fb68733a02381ad99a51ac855f28ce `
    --claude-digest 1aa454151c48cbe64f7734479739e8d637d885200d10837580e4b03c8330109e `
    --overlay-digest 355db0e5c2a36f7a3ba39fc21c25b5287c2f54f44da5beaec61775b9620416b8 `
    --codex-digest e3e366d488a8a9f0475dcb7f0e94aad500257e69f841598a1afcd495db05c698 `
    --native-json-stdin
```

2026-10-01 실제 목록은 Claude·Codex 모두 후보 5개 중 등록·활성 일치 0개,
미등록 5개였다. 목록 없이 실행하면 `native_plugin_coverage.status=not_observed`이고,
형식이 틀리면 차단한다. `metadata_matched`가 되더라도 캐시 바이트·명령
우선순위·실행·과금은 검증하지 않으며 설치 허가가 아니다.

출력의 `host_snapshot_complete`는 위 8개 링크의 관측 성공만 뜻한다.
`flat_coverage`는 SKILL.md 메타데이터 감사이며 현재 양쪽 모두
`status=gaps`, `rollout_gate=blocked`다.
위 네 고정 digest로 실행한 현재 결과는 후보 4/4 바이트 검증 성공과
Core 링크 8/8 관측이지만, 전체 flat 감사의 Claude 4/182·Codex 4/177 일치,
네이티브 등록 양쪽 0/5라는 결손은 그대로다. `full_skill_set_verified=false`,
`host_command_precedence_verified=false`, `billing_verified=false`,
`installation_ready=false`가 유지되므로 설치 승인이나 실사용 품질
증거로 사용하지 않는다. 실제 명령 선택, 호스트 적재, 구독 청구,
이미지·Grok Bot 전달은 이 검사의 범위 밖이다.

`flat_coverage.<host>.topology`는 후보 전체를 실제 선택된 설치 별칭 기준으로
물리 폴더·정션/심볼릭 링크·미설치로 나눈다. 스캐너의 해결된 대상 경로를
그대로 분류하면 정션을 물리 폴더로 오인하므로, 선택 기록의 최초 별칭을
사용한다. `shadowed_names`는 후보 이름이 여러 flat 경로에 노출된 수다.
경로 자체는 출력하지 않는다. 2026-10-01 고정 후보 감사에서 Claude는
물리 폴더 변경 133·링크 변경 1·링크 일치 4·미설치 44, Codex는 링크
변경 128·링크 일치 4·미설치 45, 후보 이름 중복 노출 1이었다. Claude의
물리 폴더 133개 중 69개는 이전 후보와 줄바꿈을 정규화하면 SKILL.md가
같았지만 64개는 내용도 달랐다. 이 차이가 사용자 편집인지 다른 버전인지는
확정하지 않았으므로 대량 이동·덮어쓰기 대상이 아니다.
`flat_coverage.<host>.asset_delta`는 선택된 물리 폴더만 중첩 디렉터리
링크를 따라가지 않고 상대 파일명으로 비교한다. 현재 Claude 물리 폴더
133개에서 설치본 전용 224파일·후보 전용 8파일·건너뛴 중첩 링크 0개,
Codex는 물리 폴더가 0개다. 설치본 전용 파일이 새 후보에서 없어지면
실제 필요한 실행 자산을 잃을 수 있다. 이 수치는 파일 바이트나 필요성,
사용자 편집 여부를 판정하지 않으며 명령 선택·실행 품질도 증명하지 않는다.

### 격리 flat 링크 전환·복원 리허설

`scripts/vibe_flat_transition.py`는 운영 설치기가 아닌 내부 테스트 라이브러리다.
고정 후보 4영수증·기존 링크 8/8·Claude/Codex 네이티브 5플러그인 등록
메타데이터가 모두 일치할 때에만 7개 flat 링크의 전환 계획을 만든다.
전환·복원 함수는 Windows 임시 디렉터리의 `vibe-flat-test-*` 바로 아래에
있는 격리 프로필만 허용한다. 기존 링크는 호스트별 archive로 이동하고
복원 시 새 링크를 quarantine에 남겨 삭제하지 않는다. `.agents` 별칭은
이동하지 않으며 Claude `/vibe` 링크를 따라간다. 중간 실패·재호출·계획
변조·부모 정션 충돌을 테스트한다.

전환 직전 격리 루트에 `vibe-flat-transition.json`을 배타적으로 만들고
계획 전체를 기록·파일 동기화한다. 기록이 이미 있으면 전환을 거부한다.
테스트는 두 번째 링크 생성 시 프로세스 중단을 흉내 낸 뒤
`recover_isolated(<격리 루트>)`가 저장된 계획을 검증해 원래 링크 7개를
복원하는지 확인한다. 복원 후에도 기록·quarantine은 증거로 보존한다.
손상·중복 키·심볼릭 링크 기록은 읽기 단계에서 거부한다.

```powershell
python -B -m unittest scripts.tests.test_vibe_flat_transition -v
```

이 코드는 실제 사용자 홈 적용 CLI, 네이티브 플러그인 설치, 설치 캐시 바이트
검증, 호스트 명령 선택, 실제 사용자 홈 적용 또는 전원 장애 후 내구성
보증을 제공하지 않는다. 격리 복구는 단일 작성자와 프로세스 중단만
검증했으며, 운영 설치 복구로 해석하지 않는다.
현재 실제 등록은 두 호스트 모두 0/5이므로 계획 단계부터 차단된다.
따라서 D-39 사용자 설치 NO-GO와 `installation_ready=false`를 변경하지 않는다.

## 2026-10-01 `/vibe` 2.12.32 최상위 Codex 크레딧 증거 가드 후보

`fix/vibe-grok-billing-261001`에서 최상위 `credits` 기록이 빠지고 명명된
한도 버킷에만 `has_credits=false`·`unlimited=false`·잔액 0이 있을 때,
계획이 `ready`가 되고 가짜 Codex CLI 전송도 진행되는 결손을 재현했다.
최상위와 각 명명된 버킷의 기록을 모두 요구하도록 고쳤고 두 회귀 테스트는
수정 전 실패, 수정 후 통과했다. 실제 계정·모델·구매 크레딧은 호출하지 않았다.

새 오프라인 후보는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-top-credit-candidate/`이다.

| 산출물 | 검증된 전체 digest | 범위 |
|---|---|---|
| `source` | `da3ec9e8fb20bfc591e2f5e2175db09b50b356a7d72fd3727ef2dfcb8bcce06f` | 137스킬·423파일 |
| `candidate-safety` | `59c4f1ef087e9b0e9ee32bc20eb7de75d1b08ab2417db053ed1772f8be0aaea6` | Claude 5플러그인·182스킬 |
| `codex-overlay-safety` | `2ace57dacc842acd147b74c4f5909ca7496a25b9c79c582d4afde6507deef481` | Codex 호환 오버레이 |
| `codex-subset-safety` | `4ef543c0223f938a9127ce9c6bbca3ac3565e9b79f04e3eddd538e935e59b486` | Codex 177스킬·출처 검증 |

네 영수증 재검증, 오프라인 probe 4/4, `/vibe` 단위 테스트 327건,
자체 점검 180항목, 스킬 품질 141/141, 라우팅 표 동기화가 통과했다.
고정 플러그인 커밋을 별도 복제본에서 포장했으며 원본 저장소의 브랜치나
사용자 설치본을 바꾸지 않았다. 정확한 새 후보의 별도 Windows Sandbox
두 곳에서 네트워크·클립보드·장치 리디렉션과 인증정보 없이 적재·복원을
단발 검증했다. Claude Code 2.1.285는 5플러그인·182스킬·디버그 오류0,
Codex CLI 0.155.0은 5플러그인 활성. 두 게스트 모두 이전 링크 Claude5·
Codex2개를 두 번 복원하고 시험 플러그인 최종0, 활성 네트워크0·모델 생성0이었다.
두 게스트 종료 후 `wsb.exe list --raw`는 빈 목록이고 네 후보 영수증도
다시 일치했다. 원시 결과는 후보 `host-rehearsal/claude-output/integrated-result.json`
(SHA-256 `36855567b0c16b691de5806fbdfe94dd925204884138cdf2a0b7624f708e4651`)과
`host-rehearsal/codex-output/codex-integrated-result.json`
(SHA-256 `69db36700cbadd2ef02f1a7a84c33c738b1d4dbebe6da8bf2e7e8e52c960ae8f`)이다.
이것은 무인증 호스트 적재·복원만 증명하며 실제 구독 청구,
모델·이미지·Bot 호출, 자동 선택 품질과 전체 외부 런타임은 미검증이다.
`installation_ready=false`, `host_compatibility_verified=false`,
`runtime_closure_verified=false`를 유지한다. PR #68·#69의 독립 리뷰와
§35 별도 심판 D-code 없이 `main` 머지하지 않는다.

## 2026-10-01 `/vibe` 2.12.30 이미지 청구 관측값 가드 후보

`fix/vibe-grok-billing-261001`의 `2ec27c7`은 이미지 호스트 도구의
`billing` 관측값이 `null`·배열·문자열일 때 쿼터 대조에서 예외가 나던
경로를 차단 판정으로 바꾼다. 회귀 테스트에서 수정 전 세 예외를 재현하고
수정 후 `IMAGE_SUBSCRIPTION_HARD_CAP_UNVERIFIED` 및
`IMAGE_QUOTA_UNVERIFIED`로 차단되는 것을 확인했다. 새 후보는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-image-billing-guard-candidate/`이며,
이전 2.12.29 후보와 사용자 홈은 그대로 보존했다.

| 산출물 | 검증된 전체 digest | 범위 |
|---|---|---|
| `source` | `86ecf72755a5481fae387168b71b369cb53f0bb455a831ad8654961cd4a4ce6c` | 137스킬·423파일 |
| `candidate-safety` | `d95f12754bc5215cc3037484fc0364ef0aee23250aa934417be006225cb149b7` | Claude 5플러그인·182스킬 |
| `codex-overlay-safety` | `5d935f47215fffc657e252f77c158d2ebe50f47ce7dd2256457f88675079052d` | Codex 호환 오버레이 |
| `codex-subset-safety` | `db86739d0a71ee713e1d9a09ce12b482be778abac84aa4416d4af6a3683bdcb3` | Codex 안전 부분집합 177스킬 |

네 영수증 재검증과 Claude 후보의 오프라인 probe **4/4 단계**가 통과했다.
이 probe는 Claude 후보 구조를 요구하므로 `source`·Codex 오버레이·부분집합에
직접 실행한 세 건은 입력 종류 불일치로 차단됐으며 통과 건수에 넣지 않는다.
`test_orchestrate.py` 119개, 이번에 실행한 오프라인 단위 테스트 합계 387개,
`selftest.py` 180항목, 스킬 품질 141/141, Node 플러그인 검증 68스킬이 통과했다.
새 후보의 무인증·네트워크 차단 Windows Sandbox 두 곳에서 Claude Code
2.1.285는 플러그인 스킬 182개를 오류 0으로 로드했고, 고정 Codex CLI
0.155.0은 플러그인 5개를 활성화했다. 이전 Claude 5개·Codex 2개 링크의
두 차례 복원과 시험 플러그인 최종 0개가 양쪽에서 통과했다. 원시 결과는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-image-host-rehearsal/`
의 `claude-output/integrated-result.json`(SHA-256
`6aff5b4562fce02024837c03bdd01c6e8c7f71917a199d56dc8b1115fbbba2ec`)과
`codex-output/codex-integrated-result.json`(SHA-256
`9612c5a3e369e78911df135b07a6a1571f8990b467932ea1bef441fe4e1cce15`)다.
게스트 인증 환경변수·활성 네트워크·모델 생성은 0, 종료 후 Sandbox도 0개였다.
후보 번들·subset 영수증은 격리 시험 후에도 일치했다. 정적 콘텐츠 대조는
공통 스킬 176개·payload 620파일 동일, Codex 안전 제외 5개·투영 1개이며,
경로 감사의 내부 누락·비이식 명령은 양쪽 0이다. 다만 외부 Gstack 런타임
힌트는 Claude 31/Codex 30스킬에 남아 `external_runtime_pending`(종료 1)이다.
이 호스트 시험은 빈 게스트의 적재·복원 증거에 한정된다. 실제 사용자
프로필의 스킬 선택, 이미지 생성·Grok Bot 배달, 모델/effort 선택 품질과
구독 청구는 실행·입증하지 않았다.
`installation_ready=false`, `host_compatibility_verified=false`,
`runtime_closure_verified=false`, `selection_quality_verified=false`를 유지한다.
PR #69의 독립 리뷰와 §35 별도 심판 D-code가 없으므로 운영 자동 배포 허용에도
`main` 머지는 보류한다.

## 2026-10-01 PR #68·#69 누적 `/vibe` 2.12.29 이전 후보

이전 검증 후보는 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-credit-failclosed-candidate/`이다. PR #68 코드 커밋 `c17ba6b`의 Codex 구매 크레딧 fail-closed 수정과 종속 PR #69 검증 기준 코드 커밋 `0207301`의 Grok ACP 초과 과금 필드 수정이 누적됐다. 이 절의 문서 전용 후속 커밋은 후보의 `skills-src` 바이트를 바꾸지 않는다. 두 PR은 Draft이며 이번 변경의 독립 코드 리뷰와 §35 별도 심판 D-code가 없어 `main`에는 반영하지 않았다. Simon의 Cloudflare Pages 운영 자동 배포 허용은 유효하지만 이 품질 게이트를 면제하지 않는다.

후보의 source 137스킬·423파일 digest는 `2fb0fa29881a1f9f8607d33eec0db923bbab10a47f212cfa59fbde330ee6de98`, Claude 5플러그인·182스킬 digest는 `eb55167bac1dab41b9c93203cd3400f41121c7eb49c7a08c8f73df1dd8310e1d`, Codex overlay digest는 `563fb61b8cd1b4b9530b842d6a660e9bba3f62724ff356983603d9d22ac052f0`, Codex 안전 부분집합 177스킬 digest는 `f12c0f280aa6c455323f91aa0111b2fcb65701f8e350dbac5d6c61b20a9a9ffa`다. 네 영수증과 오프라인 probe 4/4, `/vibe` 누적 테스트 326/326, 스킬 품질 141/141이 통과했다. PR #68의 `c17ba6b` 및 PR #69의 `0207301` 코드 커밋에서 CI는 각각 4/4 성공했다. 문서 전용 후속 HEAD의 CI는 별도 확인 대상이다.

격리 호스트 원시 기록은 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-credit-host-rehearsal/`에 있다. 네트워크·클립보드·장치 리디렉션 OFF, 인증·사용자 홈 비매핑의 별도 Windows Sandbox에서 Claude Code 2.1.285가 5플러그인·182스킬, Codex CLI 0.159.0이 5플러그인을 로드했다. 양쪽 모두 이전 Claude 5개·Codex 2개 링크를 두 번 복원하고 시험 플러그인을 제거했으며, 모델 생성 0·종료 후 게스트 0이었다. 이 시험 단독으로는 사용자가 고정한 Codex 0.155.0의 호환성이나 운영 프로필 자동 선택을 입증하지 않는다.

고정 Codex 0.155.0의 별도 원시 기록은 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-codex0155-host-rehearsal/`에 있다. 실행 파일 SHA-256 `e4c11374bd9de8ad5c3b7617fd4654bb7839901edb0863f9930666863c7a021b`를 읽기 전용 매핑한 무인증·네트워크·클립보드 차단 Sandbox에서 후보 플러그인 5개가 활성화됐다. 기존 Claude 링크 5개와 Codex 링크 2개를 두 번 복원한 뒤 시험 플러그인 0개를 확인했다. 게스트 인증 환경변수 0·활성 네트워크 어댑터 0·모델 생성 0이며, `output/codex-integrated-result.json` SHA-256은 `56d1057c364c409454ad7d60c80a3ccf4085213ce55596c3baab418077a43ecb`다. 게스트 종료 후 실행 인스턴스는 0개였다. 이 결과는 실제 사용자 프로필 설치·자동 스킬/모델/effort 선택·구독 청구까지 검증하지 않는다.

2026-10-01 06:59 KST 확인한 Bot 명단은 2026-09-24 사용자 제공 스냅샷 19개 전부가 `active - reported … live access unverified`로, 정확한 `active`는 0개였다. Relay STATUS의 마지막 시각은 2026-09-27 17:35 KST다. 중앙 발송 어댑터는 이 상태를 거부하며 관련 27개 테스트가 통과했다. 현재 이미지 도구에는 구독 전용 USD 0 제공자 하드캡·요청 ID 재조회 계약이 없고, Gstack 외부 런타임은 Claude 31/Codex 30스킬에서 pending이다. 따라서 사용자 홈 설치·실제 모델/effort 자동 선택·구독 청구·이미지 생성·Bot 배달은 **미검증**이다. `runtime_closure_verified=false`, `host_compatibility_verified=false`, `selection_quality_verified=false`, `installation_ready=false`를 유지한다. 상세는 후보 `report.html`에 있다.

## 검증된 소스 오버레이 — 격리·오프라인 경로

`/vibe` 이관의 새 배포 경로는 **source-owned overlay**입니다. 아래 명령은 실제
사용자 설치나 공식 5-plugin release를 교체하지 않습니다. 기존 기본 설치기와
SessionStart 자동 복사 경로는 아직 아래 계약으로 전환되지 않았습니다.

`distribution/skills-release.v1.json`이 배포용 소스 137개의 단일 plugin home을
명시합니다. 개발용 4개는 제외 범위로 기록하고, 공식 plugin에만 있는 45개도
포함하거나 삭제하지 않습니다. 숫자는 이 manifest 기준이며 새 스킬을 추가하면
소유권도 함께 갱신해야 합니다. 미배정 source는 빌드가 실패합니다.

Windows의 Python 3.10+와 Git으로, 존재하는 격리 부모 폴더 아래 **새 절대 경로**를 지정합니다.
예시 경로는 실제 환경의 임시 경로로 바꾸세요. 출력 위치가 이미 있으면 빌드는
덮어쓰지 않고 실패합니다.

```text
python -B scripts/skill_release.py build --repo E:/reviewed/SimonK-stack --ownership E:/reviewed/SimonK-stack/distribution/skills-release.v1.json --output E:/staging/release-a
python -B scripts/skill_release.py verify --package E:/staging/release-a --expected-digest <build가 반환한 release_digest>
```

빌드는 Git 추적 중인 `skills-src/<name>/` 전체 파일과 LICENSE/NOTICE,
`skills-src/VENDORED.md`의 upstream attribution을 복사합니다.
`release.json`에는 source/package/flat-install 상대경로, 바이트 수, SHA-256,
Git 실행 비트가 들어갑니다. 캐시·`.env`·백업·symlink/reparse·hardlink·충돌·경로 탈출은
포장하지 않습니다. 파일은 읽기 전에 열린 핸들의 hardlink 수까지 검사합니다.
미추적 파일은 배포물에 포함되지 않으므로 필요한 새 helper/assets는 먼저 Git에
추가하세요. SKILL.md가 있는 미추적 새 스킬 자체는 소유권 검사에서 차단됩니다.

`release_digest`는 검토한 빌드 결과에서 별도로 보관해야 합니다. 공격자가 package와
동시에 바꿀 수 있는 manifest의 자체 hash를 신뢰하는 서명/인증 체계가 아닙니다.
이 artifact는 명시한 tracked working-tree bytes의 snapshot이며 Git commit 전체나
공급망 출처를 인증하지 않습니다. 소스 snapshot과 임시 staging의 단독 작성이
전제입니다. 빌드·materialize 중 다른 작성자가 해당 트리를 수정하지 않아야 합니다.

기존 `install.sh`를 통해 격리된 flat skill root로 연결합니다. 이 명시적 모드는
backup/clone/의존성 설치/환경변경/marker 기록보다 먼저 끝납니다. `--force` 등
legacy 옵션 혼용은 실패하고, 옛 설치 경로로 자동 fallback하지 않습니다.

```bash
# 기본 preview: target 생성·설정 변경 없음
bash scripts/install.sh --offline-package E:/staging/release-a --target E:/staging/skills-a --expected-digest <digest>
# 전체 검증 후 새 격리 target에만 공개
bash scripts/install.sh --offline-package E:/staging/release-a --target E:/staging/skills-a --expected-digest <digest> --apply
```

Git Bash의 Python 경로가 다르면 이 명령에만 `SIMONK_PYTHON`을 지정할 수 있습니다.
검증·읽기·쓰기·publish는 현재 Windows 고정 로컬 드라이브 전용이며,
UNC/장치 경로·네트워크 드라이브·다른 플랫폼은 실패로 차단합니다.
보호 경로와 입력/출력 중복 검사는 핸들에서 얻은 정규 경로를 비교하므로
Windows 8.3 짧은 경로 별칭으로 우회할 수 없습니다.
부모/파일/stage의 native handle을 고정하여 reparse 경로 바꿔치기와 stage 교체를
막고, 같은 부모 안에서 no-replace 원자적 directory publish를 수행합니다.
publish 전후 owned 파일을 검증하지만 같은 사용자에 의한 동시 child 추가를
OS 권한으로 봉쇄하는 기능은 아닙니다. 위 단독 작성 전제와 구분하세요.
Windows는 Git의 portable 실행 비트를 기록하지만 실제 POSIX executable 권한 검증은
할 수 없어 `mode_verified=false`입니다. bytes 검증과 이를 구분하세요.

같은 artifact로 다시 실행하면 이미 설치된 **실제 owned 파일**을 다시 검증할 뿐
쓰지 않습니다. 다른 release, 수정/추가/누락된 owned 파일, 기존 unmanaged target은
보존하고 실패합니다. 별개의 unowned 최상위 폴더는 읽거나 바꾸지 않습니다.
실제 `.claude/.codex/.agents`, 공식 `SimonK-Plugins`, gstack 및 reparse target은
이 경로의 적용 대상이 아닙니다. 실제 운영 이관은 별도 검토·승인 단계입니다.
중단 시 완성 전 임시 `.simonk-build-*`/`.simonk-materialize-*`는 부모에 남을 수
있지만 기존 destination을 삭제하거나 교체하지 않습니다. 자동 정리/롤백은 없습니다.

이 검증은 **포장된 파일 전체의 무결성**입니다. repo-root PowerShell wrapper,
`~/.claude/scripts/upgrade-vendor.sh`, 외부 vendor/runtime/CLI/API/MCP/인증/과금,
호스트별 SKILL frontmatter 호환성 및 스킬 행동 평가까지 닫힌 의존성 검증이 아닙니다.
빠진 외부 의존은 manifest에 명시하며, 모델·Bot을 실행하거나 설치하지 않습니다.
공식 plugin의 extras/manifest는 아래 별도 candidate 경로에서 검증합니다.
자동 설치기의 정합성, 실제 재설치·main 통합은 후속 배포 게이트로 남습니다.

`simonk` 2.1.0부터 skill-local `simonk/scripts/simonk.ps1`은 overlay와
Core candidate에 포함됩니다. 별도 source checkout 없이 같은 배포의 sibling
`vibe/scripts/orchestrate.py`로 오프라인 계획만 전달합니다. 기존 repo-root
helper와 프로필의 hash pin은 그대로이며, 아래 예제는 프로필 설치가 아닙니다.

```powershell
$ErrorActionPreference = 'Stop'
. '<candidate>/plugins/SimonKCore/skills/simonk/scripts/simonk.ps1'
simonK -RequestPath request.json -RuntimePath runtime.json
exit $LASTEXITCODE # 배치 스크립트에서만 사용; 대화형 셸에서는 상태만 확인
```

온전한 five-plugin candidate는 receipt에 묶인 5개 catalog를 기본 탐색합니다.
분리된 plugin 배치나 flat skill root에서는 검토한 전체 catalog를 `-Root`로
명시합니다. `/vibe` 코디네이터가 현재 호스트에서 실제로 노출·허용된 경로를
조합하며, 이미 확인 가능한 경로를 사용자에게 매번 입력하도록 요구하지 않습니다.
inventory의 scope·충돌·digest를 확인하고 같은 순서의 root를 plan에 전달합니다.
캐시 버전 경로 추측·전역 registry 자동 스캔·설정 저장은 추가하지 않습니다.
**PS `-Root`에는 exclusion 전달이 없습니다.** 읽기 허용된 전용 plugin root에만
사용하고, 보호 경로 제외가 필요하면 Python `plan --root ... --exclude-root ...`를
직접 사용하세요. 사전 inventory의 제외가 PS 호출에 자동 적용되지는 않습니다.
상세는 `vibe/references/orchestration.md`의 split-home 절차를 따릅니다.
이는 코디네이터 절차이며 실제 호스트의 자동 수집 adapter·설치 검증 완료가 아닙니다.
`-RegistryPath`는 신뢰한 중앙 registry 입력만 지정합니다.
이 경로의 테스트는 synthetic runtime으로 수행하며 실제 모델·과금·설치 증명이
아닙니다. 전체 runtime closure는 아직 별도 게이트입니다.
이 추가로 readiness 플래그를 true로 바꾸지 않습니다.

`multi-terminal-dispatcher` 1.1.0은 skill-local PowerShell entry를 포함합니다.
기존 repo-root `scripts/multi-terminal-launch.ps1`은 같은 typed parameter를
유지하며 해당 entry에만 위임합니다. 배포 후보에서는 source checkout 없이:

```powershell
pwsh -NoProfile -NonInteractive -File '<candidate>/plugins/SimonKCore/skills/multi-terminal-dispatcher/scripts/multi-terminal-launch.ps1' -PlanPath plan.json -DbPath state.sqlite3 -Action preview
```

이 preview는 이미 등록된 plan/DB를 필요로 하며 모델·Orca 호출이나 논리 행
갱신을 하지 않습니다. 그러나 SQLite read/write 열기와 `BEGIN IMMEDIATE`로
쓰기 잠금을 사용하므로 파일시스템 읽기 전용이나 무경합 조회는 아닙니다.
DB·run을 새로 만들거나 certificate를 만들어주는 설치/준비 명령이 아닙니다.
`dispatch`/`reconcile`은 별도 실행 권한과 runtime/account 검증이 필요합니다.
root facade의 canonical 파일이 없으면 입력 오류보다 helper 부재를 먼저
보고하며 다른 설치본으로 fallback하지 않습니다. 실제 설치·호스트 활성화는
이 예제나 파일 무결성 검증으로 승인되지 않습니다.

회귀 테스트: `python -B -m unittest discover -s scripts/tests -p test_skill_release.py`
(임시 Git repo·격리 target, 실제 사용자 홈/공식 plugin/모델 호출 없음).

### Manifest 계약과 새 체크아웃 재현성

`schema_version`은 정수 1만 허용하며 bool/실수는 거부합니다. `source_state`는
`tracked-working-tree-bytes`만 허용하고, 외부 의존 선언은 정확한 `name/status`
문자열 두 필드·필드당 1~4096자·고유한 이름으로 제한합니다. 선언 순서는 보존합니다.
NaN/Infinity/overflow·중복 JSON 키·비정규 release.json은 검증에서 거부합니다.
release.json은 builder의 UTF-8/sorted-key/2-space/trailing-newline 형식이어야 합니다.
이는 형식 검사이지 의존 상태 문자열의 진실성이나 공급망 출처를 인증하는 기능은 아닙니다.

`.gitattributes`는 **새 체크아웃**의 배포 텍스트 확장자(md/json/py/sh/ps1/sql/html),
LICENSE/NOTICE 및 scripts/install.sh에만 LF를 지정합니다. 알려지지 않은 packaged
asset은 `-text`로 바이트를 보존합니다. 기존 작업 폴더를 일괄 renormalize하지 마세요.
일반 build는 dirty 상태도 가능한 현재 raw snapshot이며 clean commit attestation이 아닙니다.
같은 commit이어도 기존 CRLF 작업 폴더와 새 LF 체크아웃은 서로 다른 **정상 digest**를
만들 수 있습니다. 이전 패키지를 무효화하거나 기존 checkout과 같다고 주장하지 않습니다.

테스트는 두 개의 독립 임시 Git checkout에 checkout **전** `core.autocrlf=true/false`를
각각 적용하여 전체 package bytes/digest 일치, binary 원본 보존, 실제 Git Bash
installer의 preview/apply/재검증을 확인합니다. fixture만 설치하며 실제 홈은 건드리지 않습니다.

`.github/workflows/skill-release-windows-manual.yml`은 같은 정확 HEAD의 **실제 소스**를
두 새 로컬 clone으로 검증할 수 있는 Windows workflow 정의입니다. `workflow_dispatch`
전용·contents:read·credential persistence 없음·artifact upload/배포 없음입니다.
이 정의를 추가했다고 원격 CI가 통과한 것은 아닙니다. 과금 조건 확인과 별도 실행 권한
없이는 실행하지 마세요. 결과는 같은 SHA·선언된 checkout 정책 아래의 재현성만 증명합니다.
배포 전에는 commit과 artifact를 결합하는 별도 provenance receipt/승인도 필요합니다.

## 공식 5-plugin 배포 후보 — 설치·활성화 아님

`scripts/plugin_bundle.py`는 verified source overlay와 **로컬의 pinned 공식 저장소
5개**를 결합하여 새 격리 폴더에 Claude-format candidate를 만듭니다. 현재 입력은
`distribution/plugin-inputs.v1.json`의 정확 HEAD이며, 변경된 HEAD를 자동 수용하거나
fetch/pull하지 않습니다. 실제 홈·공식 plugin 폴더를 출력 대상으로 지정할 수 없습니다.

```text
python -B scripts/plugin_bundle.py build --source-package E:/staging/release-a --source-digest <source release_digest> --plugin-parent E:/reviewed/SimonK-Plugins --inputs distribution/plugin-inputs.v1.json --output E:/staging/plugins-candidate-a
python -B scripts/plugin_bundle.py verify --package E:/staging/plugins-candidate-a --expected-digest <build가 반환한 전체 bundle_digest>
```

소스 137개와 plugin-only 45개를 합쳐 182개의 단일 home을 검사합니다. 현재 분포는
AIHub 7 / Core 61 / Design 22 / Market 32 / Stack 60입니다. source-owned 폴더는
source member와 정확히 일치해야 하며, 원본에 source가 설명하지 못하는 supplemental
파일이 있으면 버리지 않고 빌드를 차단합니다. source의 frontmatter·hooks·명시호출
정책·파일 bytes·Git mode는 바꾸지 않습니다.

3,873개 pinned base 경로를 copied/replaced/transformed/excluded 중 하나로 전수
분류합니다. plugin-only 파일, 안전한 공식 agents/commands/.github/루트 문서·LICENSE/
NOTICE를 보존하고, source LICENSE/NOTICE/VENDORED는 각 plugin의
`.simonk-source-attribution/`에 별도로 둡니다. AIHub `legacy/` 3,292개와 대응 `.py`가
있는 CPython 캐시 7개는 payload에서 제외하되 Git blob/mode/path/이유를 기록합니다.
미분류·위험 파일·캐시 원본 부재·중복 소유권·manifest 목록 차이는 실패합니다.
manifest/agent/command와 plugin-only의 알려진 text 파일에서 legacy/cache를 명시
참조하면 차단합니다. 이는 보수적인 text 검사이며 동적 런타임 의존 해석은 아닙니다.

`bundle.json`은 원본 metadata bytes, 원본 Git commit object, 전체 base inventory,
source manifest와 source digest, output의 origin/input path/hash/size/mode를 보관합니다.
package-only verifier는 Git tree Merkle root와 commit SHA를 다시 계산해 base 경로
누락을 검출하고, 모든 source member·각 home의 attribution과 정확히 대조합니다.
**이 연결은 Git inventory의 증명이지 raw working-tree bytes가 blob과 같다는 증명이
아닙니다.** clean status도 filter/EOL/assume-unchanged 설정을 넘어선 blob attestation은
아닙니다. 검토한 전체 `bundle_digest`를 별도로 고정해야 하며 서명 체계는 아닙니다.

후보는 원본 plugin.json의 version/skills와 self-marketplace의 두 version만 변환합니다.
D-76 4단계부터는 SimonKCore·SimonKStack plugin.json의 description 끝에 고정 안내문
(`plugin_bundle.DESCRIPTION_NOTICES`: 레거시 이전 명령 4줄, 안전 훅 Windows 전용)을
덧붙입니다. 스킬 목록·개수는 바뀌지 않습니다.
`<base-version>-vibe.<source-digest 앞 12자>`는 후보 표시일 뿐 고유 검증키나 설치
방지 장치가 아닙니다. 원본 JSON과 변환 후 JSON을 모두 검증 기록으로 보존합니다.
이 candidate envelope를 marketplace에 등록하거나 `install.sh` 입력으로 넘기지 마세요.
배포용 빌드는 `--release-version`으로 아래 릴리스 버전을 씁니다.

### 릴리스 버전과 콘텐츠 식별 (D-76 2단계)

`--release-version`을 주면 다섯 plugin.json과 self-marketplace의 version이 모두 그
값이 됩니다. 값은 `python -B scripts/dist_release.py version --repo .`이 계산하는
`1.<N>.0`이고, N은 빌드한 커밋의 `git rev-list --count HEAD`(전체 이력)입니다.

- **단조 증가**: main에 커밋이 더해지면 N은 반드시 커집니다. 조상 전체를 세므로
  merge·squash·fast-forward 어느 쪽이든 줄지 않습니다(first-parent 수는 줄 수 있음).
- **재현성**: 같은 커밋은 언제 다시 빌드해도 같은 version, 같은 바이트입니다.
  `run_number`는 같은 커밋에도 다른 version을 주고 워크플로 이름을 바꾸면 1부터
  다시 셉니다. 날짜 기반은 하루 안의 순번을 따로 저장해야 해서 택하지 않았습니다.
- **pin만 바꿔도 새 version**: pin 변경은 `distribution/plugin-inputs.v1.json`을 바꾸는
  main 커밋이므로 N이 올라갑니다.
- **레거시보다 위**: 첫 값부터 레거시 루트 플러그인 `0.1.0`과 pin 원본 version(0.x)보다
  큽니다. 빌더는 pin 원본 version 이하를, `version` 명령은 레거시
  `.claude-plugin/plugin.json` 이하를 거부합니다.
- **SemVer 본체만**: `-`·`+` 꼬리를 쓰지 않습니다. 기존 `-vibe.018825543742`는 0으로
  시작하는 숫자 식별자라 SemVer가 아니고 `0.1.0`보다 낮게 정렬됩니다. 호스트가
  `+digest`를 어떻게 다루는지는 확인되지 않았습니다.
- **얕은 clone 거부**: 얕은 clone은 N을 적게 셉니다. 이 PC의 공유 clone은 561,
  GitHub main은 754였습니다(2026-10-04). `version` 명령은 얕은 clone이면 멈춥니다.
- **이력을 다시 쓰면**(force push) N이 줄 수 있습니다. 그때는 `dist_release.py`의
  `EPOCH`(첫 자리)를 올립니다. publish 단계도 dist보다 낮은 version을 거부합니다.

콘텐츠 식별은 `bundle.json`의 `release.content_digest`입니다. source digest, 다섯 pin
커밋, safety projection, 출력 파일 전체(경로·SHA-256·mode)를 묶고, 메타데이터 10개는
version 칸을 비운 값으로 셉니다. version만 다른 두 빌드는 같은 값이고, pin만 바뀌면
트리가 같아도 다른 값입니다. 빌더 변환 코드가 바뀌어 출력이 달라져도 다른 값입니다.
`verify`가 다시 계산해 대조합니다.

`--release-version`을 빼면 기존 로컬 후보 표시 `<base>-vibe.<digest>`를 그대로
만듭니다. `update-local.ps1` 파이프라인과 기존 영수증 검증이 그대로 동작하며, 이
표시는 배포에 쓰지 않습니다.

### dist CI·게시·롤백 (D-76 3단계)

`.github/workflows/five-plugin-dist.yml`(windows-latest; main push, workflow_dispatch,
빌드 입력 경로를 건드린 PR)이 하는 일:

1. clone 전에 `core.autocrlf=false`를 걸고 전체 이력을 받습니다.
2. 다섯 pin을 공개 저장소 `github.com/Simon-YHKim/<Owner>`에서 고정 커밋으로
   `fetch --depth 1` 후 detached checkout합니다. 로컬 `plugin-pins-lf`(로컬 clone을 그
   커밋으로 checkout한 LF 작업 트리)와 같은 모양입니다. 2026-10-04 이 PC에서 같은
   절차로 받은 다섯 개는 `plugin-pins-lf`와 트리 해시·파일 바이트가 모두 같았습니다
   (diff 0, CRLF 0).
3. 빌더 4개: skill_release → plugin_bundle `--safety-adapter --release-version` →
   codex_overlay → codex_safe_subset.
4. 그 트리 그대로 경로 감사 2종(Claude 후보·Codex subset)과, 패키지된 SimonKCore·
   SimonKStack 안전 런타임으로 `test_safety_runtime`을 돌립니다. 병렬 job은
   `test_dist_release`·`test_plugin_bundle`·`test_codex_overlay`·`test_codex_safe_subset`·
   `test_safety_hooks`·`test_safety_runtime`을 같은 커밋에서 돌립니다.
5. 영수증(bundle.json, source·overlay·subset 영수증, pins.json, 감사 보고서,
   RELEASE.json)을 artifact로 90일 보관합니다. PR 실행은 여기까지(검증 전용)입니다.

**publish job은 꺼져 있습니다.** 게시 열쇠는 두 개이고 둘 다 있어야 합니다(D-82 후속 1).

1. **저장소 변수 `SIMONK_DIST_PUBLISH`가 `true`.** 지금은 설정하지 않았으므로 job 자체가
   SKIPPED입니다. PR 실행은 변수와 관계없이 게시 job에 닿지 않습니다.
2. **빌드한 커밋에 커밋된 승인 기록 `distribution/dist-publish.allow`.** publish job이
   artifact의 `RELEASE.json`을 받아 `dist_release.py gate`로 대조하고, 통과하지 못하면
   트리를 받기 전에 실패합니다. 지금은 이 파일이 없습니다(`test_dist_release`가 확인).

**D-33 hold는 더 이상 게시를 막지 않습니다.** `distribution/main-source-only.hold`는 그대로
남아 아래 둘을 계속 막습니다. 카탈로그는 2026-10-05 D-82 마지막 단계에서 다섯 `dist` 플러그인으로
전환했습니다(아래 "카탈로그 전환" 참고).

| hold를 읽는 곳 | 막는 것 |
| --- | --- |
| `.claude/hooks/session-start.sh` | SessionStart 부트스트랩 전체(Gstack 설치, 레포 스킬의 `~/.claude` 복사, instincts 시드, CLAUDE.md 생성)와 업데이트 확인 |
| `.github/workflows/release.yml` | main push마다 만들던 태그와 GitHub Release |

**카탈로그 전환(2026-10-05, D-82 마지막 단계).** `.claude-plugin/marketplace.json`은 이제 레거시
`simonk-stack` 한 항목(`313c04b` pin)이 아니라 다섯 항목입니다. 각 항목은 `git-subdir`, url
`https://github.com/Simon-YHKim/SimonK-stack.git`, path `plugins/<Owner>`, ref `dist`이고, sha와
version은 넣지 않습니다. 이 파일은 HTTPS 검증에 쓴 임시 카탈로그와 바이트가 같습니다(sha256
`24d58b0f3347…`). 전환 전에 실제 GitHub `dist`로 다음을 확인했습니다(허브 D-82·D-84).

- 깨끗한 설치: 1.765.0, 767/767 바이트 일치
- 레거시 0.1.0 이전: 사라진 스킬 0
- 원격 설치본 세션 스모크
- 내용 변경 업데이트: 1.765.0 → 1.766.0
- 고버전 재출하 롤백: 1.766.0 → 1.767.0, 내용이 1.765.0과 같음
- 다시 적용: 1.768.0
- 실제 게시 경로의 늦은 옛 빌드: 내용이 다르면 `not-newer-than-dist`로 거부, 같으면 skip

`test_main_release_fence`가 이 다섯 항목 형태를 지키고, hold를 읽는 곳이 위 두 파일뿐인지도
확인합니다. 운영 규칙은 그대로입니다. **main의 카탈로그 커밋은 되돌리지 않습니다.**

승인 기록 형식(JSON, 다섯 키만 허용):

```json
{
  "schema_version": 1,
  "scope": "five-plugin-dist-v1",
  "decision": "D-<번호>",
  "source_commit": "<세션 실측한 후보의 main 커밋, 40자>",
  "content_digest": "<그 후보 bundle.json의 release.content_digest, 64자>"
}
```

- **승인 범위**: `source_commit`이 빌드 커밋 자신이거나 그 조상이고, 빌드 콘텐츠의
  content_digest가 기록과 같을 때만 게시합니다. 승인 기록을 넣는 커밋은 후보보다 늦으므로
  빌드 커밋 하나를 적을 수 없습니다. version(`1.<N>.0`)도 커밋마다 바뀌어 승인 키로 쓰지
  않습니다. content_digest는 version 칸을 비운 값이고 빌더 넷은 승인 파일을 읽지 않으므로,
  그 사이에 빌드 입력(`skills-src/`·LICENSE·NOTICE·다섯 pin·빌더 코드)이 바뀌지 않았다면
  승인 기록 커밋을 빌드해도 후보와 같은 값이 나옵니다.
- **승인 뒤 다른 콘텐츠**: main에 빌드 입력이 바뀐 커밋이 머지되면 publish job은
  `content-not-approved`로 실패하고 dist는 그대로입니다. 그 콘텐츠를 내려면 새 결정 코드로
  기록을 고치는 PR을 머지하고, 아니면 변수를 끕니다. 내용이 다른 게시(아래 3단계의 업데이트·
  재출하 시험 포함)마다 기록이 하나씩 남습니다.
- **거부 사유**(exit 1): `no-approval`(빌드 커밋에 기록 없음. 작업 트리에만 있는 파일은 세지
  않음), `content-not-approved`, `source-outside-approval`(기록의 커밋이 빌드 커밋의 조상이
  아님). 형식 오류·없는 커밋·얕은 clone·빌드 커밋과 다른 체크아웃은 exit 2로 막힙니다.

**D-82가 정한 순서**(앞 단계가 통과해야 다음으로 갑니다):

1. **세션 확인** — 기존 로컬 dist로 최종 후보를 격리된 로그인 Windows 호스트에 설치하고,
   careful/freeze의 허용·차단·해제, 훅 로딩, 안내된 수동 이전 후 5플러그인 가용성을
   확인합니다. 기존 update가 dependencies를 채워 준다고 가정하지 않고, 모델 턴 추가 과금
   0을 먼저 확인합니다.
2. **dist만 게시, 카탈로그는 그대로** — 증거를 확인한 뒤 그 후보의 소스 SHA·digest로 승인
   기록을 PR로 머지하고 변수를 켭니다. `marketplace.json`은 바꾸지 않습니다.
3. **HTTPS 검증** — 최종 카탈로그와 바이트가 같은 임시 카탈로그로 깨끗한 설치, 레거시 이전,
   출하 내용이 바뀐 업데이트, 고버전 재출하 롤백을 실제 게시 경로에서 확인하고, 늦은 옛
   빌드 거부도 기록합니다. 로컬 `decide` 시험만으로 CI 검증 완료라고 하지 않습니다.
4. **카탈로그 전환** — 원격 설치본의 세션 스모크까지 통과한 후보로 `marketplace.json`을
   바꿉니다. 실패하면 전환하지 않고 변수를 끕니다. 이미 설치한 사용자는 검증된 고버전
   재출하와 업데이트 안내로 복구합니다.

hold 제거, SessionStart 홈 복사와 `release.yml` 재개는 이 순서에 없는 별도 결정입니다.

두 열쇠가 다 맞으면 `dist` 브랜치에
`plugins/`·`RELEASE.json`·`.gitattributes`(`* -text`, 호스트의 autocrlf가 셸 훅을 CRLF로
바꾸지 않게)를 추가 커밋합니다. 강제 push는 하지 않습니다. content_digest가 dist와
같으면 건너뛰고, dist보다 낮거나 같은 version이면 거부합니다. 게시는 동시성 그룹으로
한 번에 하나씩 하고, 진행 중인 게시는 취소하지 않습니다.

**롤백은 dist를 되감지 않습니다.** main에서 문제 커밋을 revert하거나 pin을 이전 값으로
돌리는 PR을 머지하면, CI가 이전 정상 콘텐츠를 **더 높은** version(새 N)으로 다시
빌드·게시합니다. 4단계 호스트 실측(2026-10-04, Claude Code 2.1.289, 격리 설정 폴더)에서
설치된 호스트는 이 재출하를 받았습니다(`plugin update`로 1.802.0 → 1.803.0, 불량 표식이
사라지고 빌더 출력과 273/273 바이트 일치).

같은 실측에서 호스트는 **version 문자열이 다르기만 하면 낮은 값도 받았습니다.** 1.790.0을
게시하자 `1.803.0 to 1.790.0`으로 내려갔습니다. 반대로 version이 같으면 내용이 달라도
`already at the latest version`이라며 받지 않았습니다. 그래서 늦게 끝난 옛 실행이나 오래된
빌드가 사용자에게 내려가는 것을 막는 장치는 게시 쪽 `dist_release.py decide`의 거부
(dist보다 낮거나 같은 version이면 refuse) **하나뿐**입니다. 호스트는 이를 막아 주지 않으니
`decide`를 건너뛰는 수동 dist 커밋은 하지 마세요.

**카탈로그 커밋은 되돌리지 않습니다(운영 규칙).** main의 `.claude-plugin/marketplace.json`을
다섯 `git-subdir` 항목으로 바꾸는 커밋(첫 게시 때 별도 승인으로 머지)은 revert하지 않습니다.
`plugin update`와 `marketplace update`는 먼저 main에서 카탈로그를 새로 받습니다. 카탈로그가
레거시로 돌아가면 이미 설치된 SimonKCore·SimonKMarket·SimonKDesign·SimonKAIHub는 그
카탈로그에 없어 `plugin details`에서 `not found`가 되고 갱신 경로를 잃습니다(4단계 실측).
문제가 생기면 카탈로그는 그대로 두고, 위처럼 이전 콘텐츠를 더 높은 version으로 재출하합니다.

**pin 커밋은 태그로 보존합니다.** CI는 pin을 sha로 `fetch --depth 1` 합니다. 다섯 pin
커밋은 원본 저장소 main에 머지되지 않은 기능 브랜치에만 있었으므로, 그 브랜치가 지워지면
커밋이 사라져 빌드와 위의 롤백이 깨질 수 있습니다. 그래서 pin 커밋마다 annotated 태그
`simonk-pin-<YYYYMMDD>-<sha7>`를 달았습니다(태그만 push, 브랜치 push·이력 변경 없음).
`plugin-inputs.v1.json`은 `name`·`commit` 두 키만 허용하므로(`plugin_bundle.validate_inputs`)
태그는 이 표에 적습니다. **권위는 sha입니다.** 태그는 옮겨질 수 있고 sha는 바뀌지 않으므로
빌드는 계속 sha로 받고, 태그는 커밋을 붙잡아 두는 보존 앵커일 뿐입니다.

| 저장소 | 태그 | 가리키는 커밋 | 태그 시점 브랜치 |
| --- | --- | --- | --- |
| SimonKAIHub | `simonk-pin-20261004-d523b3e` | `d523b3e1cfa800ef60c690d40b7256abf5bcba1e` | `feat/model-selector-current-260929` |
| SimonKCore | `simonk-pin-20261004-24a17a1` | `24a17a1d59d03e75d3ac57643e91789cd640350e` | `fix/core-helper-closure-260927` (현재 pin) |
| SimonKCore | `simonk-pin-20261004-a07a1e9` | `a07a1e9090edfa7e0a7db57bf02de2127f8e2ccc` | 같은 브랜치 (이전 pin, 롤백용) |
| SimonKDesign | `simonk-pin-20261004-e045400` | `e045400de6fed810f38323ba6ab755e2572e64a3` | `fix/skill-validation-260927` |
| SimonKMarket | `simonk-pin-20261004-54f757f` | `54f757f8f8f6cd73b2a470c4a13417c2e268b304` | `fix/market-missing-assets-260927` |
| SimonKStack | `simonk-pin-20261004-7f866e7` | `7f866e71e3e37e147410cdc55a5a786cf19fd2b6` | `fix/skill-validation-260927` |

pin을 올릴 때는 새 커밋에 같은 형식의 태그를 먼저 push한 뒤 `plugin-inputs.v1.json`과
이 표를 고칩니다. 이전 pin의 태그는 지우지 않습니다(롤백 PR이 그 sha를 다시 받습니다).
원본 저장소의 워크플로는 태그 push에 반응하지 않습니다(`release.yml`은 main push,
나머지는 main push·PR).

2026-10-04 SimonKCore pin을 `a07a1e9`에서 `24a17a1`(SimonKCore PR #5를 같은 기능 브랜치에
squash)로 올렸습니다. 두 트리의 차이는 `skills/semantic-recall/semantic_index.py` 한
파일입니다. 기본 루트를 `SIMON_WIKI_DIR`·`SIMONK_PROJECT_DIR`(없으면 홈 폴더)에서 계산하게
바꿔 `scripts/shipped_path_exceptions.json`의 official 예외 3건을 지웠고, 남은 예외는
`vibe-bot/bots.json`의 2nd-B 클론 위치 1건입니다. 로컬 `update-local.ps1`은 새 후보를 빌드할
때 SimonKCore가 `24a17a1`인 pins 폴더가 `ReleasesDir`에 생기거나 `-PluginPins`로 지정될
때까지 `PLUGIN_PINS_REQUIRED`로 멈춥니다.

Windows 고정 로컬 드라이브만 지원하며 기존 출력은 덮어쓰지 않습니다. Git 실행 전에
working tree를 bounded/no-follow 검사하고 파일·디렉터리 및 index를 핀합니다.
실제 파일집합·Git index·pinned tree를 대조하고 `status -uno`만 사용하므로 untracked
junction을 Git의 재귀 탐색에 맡기지 않습니다. ignored untracked 파일도 허용하지 않는
엄격한 후보 입력입니다. clean filter/include/redirected worktree/alternates와 linked
worktree는 거부합니다. Git child는 상속 GIT_* override를 제거하고 global/system 설정,
lazy fetch, 허용 transport, 인증 prompt를 차단합니다. 네트워크·provider·Bot을 실행하지
않습니다. **로컬 `.git` metadata/config 자체는 신뢰된 단독 작성 입력**이어야 합니다.
config는 물리 라인 기준의 제한된 문법만 허용하며 indented section/option을 일반 INI
continuation으로 해석하지 않습니다. 모호한 다중 행 문법은 거부합니다.
Git status는 제외된 tracked 파일도 hash할 수 있으므로 excluded payload의 직접
read/copy 제외를 OS 전체 read=0 주장으로 확대하지 않습니다.

기존 공식 clone의 ignored model cache를 지워 입력을 맞추지 마세요. 필요한 경우 검토한
정확 HEAD의 새 **로컬** clone을 별도 임시 폴더에 준비합니다. 준비 단계도 global/system
Git 설정·hooks/filter와 외부 transport를 차단하고 `--no-hardlinks --no-checkout`을
사용한 뒤 checkout **전에** local `core.autocrlf=false`, `core.longpaths=true`를 명시합니다.
clone/checkout 준비는 builder가 자동 수행하는 기능이 아니며, 긴 legacy 경로가 누락된
불완전 checkout은 정상 입력이 아닙니다. 실제 공식 저장소나 전역 Git 설정은 바꾸지 않습니다.

안전 I/O와 단독 writer·중단 stage 잔존·POSIX mode 미검증 한계는 위 overlay와 같습니다.
`runtime_closure_verified=false`, `host_compatibility_verified=false`,
`installation_ready=false`는 항상 유지합니다. 기본 v1 exact-copy 후보에서
`freeze`(Stack)의 원본 Bash leaf를 직접 실행하면 같은 `skills/` 아래에
`careful`(Core) helper가 없어 fail-closed 됩니다. 그러나 **v2 safety projection은
이 leaf를 직접 훅으로 사용하지 않습니다.** Core와 Stack 각각의
`.simonk-runtime/`에 helper를 포함하고 SKILL의 훅을 Python adapter로 바꿉니다.
격리 픽스처에서 현재 v2 후보의 Stack `freeze`는 경계 안 허용·밖 차단, Core
`clear` 후 Stack 허용을 확인했습니다. 이는 호스트가 실제 훅을 로드·기동한다는
증거가 아니며 전체 runtime closure 검증도 아닙니다. Codex의
`disable-model-invocation`/Claude hooks 정책 처리, 외부 wrapper/vendor/runtime도 별도
게이트입니다. metadata 보존을 실제 host 로딩·안전정책 실행 PASS로 해석하지 않습니다.
실제 설치·SessionStart/default installer 전환·공식 version 승격·main 병합은 포함하지 않습니다.

회귀 테스트: `python -B -m unittest discover -s scripts/tests -p test_plugin_bundle.py`
(임시 5개 Git 입력·격리 후보만 사용). Claude plugin 구조의 공식 설명은
[Plugins reference](https://code.claude.com/docs/en/plugins-reference)를 참고하세요.
이 후보에 대한 native Claude/Codex validator 또는 host 실행 통과 주장은 없습니다.
현재 2.11.7 후보를 Claude CLI의 반복 `--plugin-dir`로 세션 한정 로드한
`plugin list --json`은 5개 모두 `@inline`/`scope=session`으로 표시했습니다.
같은 CLI의 일반 설치 목록 16개에는 SimonK가 0개입니다. 이는 이 후보의
manifest 발견 증거이며 스킬 호출·훅 실행·영구 설치 증거는 아닙니다.

같은 5개 `--plugin-dir` 세션에서 `claude plugin details <name>@inline`를 각각
조회하면 아래 구성요소를 열거합니다. `Skills` 행에는 이름이 같은 슬래시 명령도
포함되므로, 실제 `skills/*/SKILL.md` 182개와 `commands/*.md` 5개를 분리해
대조했습니다. 플러그인별 `Always-on` 수치는 CLI의 **추정치**이며 합산값을
실제 세션 토큰 사용량이나 라우팅 정확도 측정값으로 해석하지 않습니다.

| 플러그인 | 실제 스킬 | 명령 | 호스트 열거 | Always-on 추정 |
| --- | ---: | ---: | ---: | ---: |
| SimonKAIHub | 7 | 1 | 8 | ~1,791 tok |
| SimonKCore | 61 | 2 | 63 | ~14,017 tok |
| SimonKDesign | 22 | 1 | 23 | ~5,590 tok |
| SimonKMarket | 32 | 1 | 33 | ~7,554 tok |
| SimonKStack | 60 | 0 | 60 | ~12,628 tok |
| **합계** | **182** | **5** | **187** | **~41,580 tok** |

이 관측은 호스트의 **구성요소 열거**를 확인할 뿐, 자동 스킬 선택, 명령 호출,
SKILL 내부 훅의 실행·안전성, Codex의 실제 후보 로딩을 확인하지 않습니다.

OpenAI의 [plugin 패키징 문서](https://developers.openai.com/plugins/build/plugins)는
Claude 호환 manifest도 수용한다고 설명합니다. 로컬 `plugin-creator`의
`validate_plugin.py`는 `.codex-plugin/plugin.json` 형식만 검사하므로, 현재
Claude-format 후보 5개에 적용하면 모두 해당 파일 부재로 실패합니다. 이 결과를
Codex가 후보를 로드할 수 없다는 판정으로 해석하지 마세요. 반대로 문서상 호환성만으로
이 후보의 native 로딩, skill 선택, hooks·commands 변환이나 실행 안전성이 검증된 것도
아닙니다. 별도 격리 호스트 검증과 설치 승인 전까지 위 세 readiness flag는 그대로
`false`입니다.

Codex CLI 0.155.0의 **별도 `CODEX_HOME` 합성 fixture**에서는
`.claude-plugin/plugin.json`과 스킬 1개만 있는 플러그인을 로컬 marketplace에서
`plugin add`했고, `plugin list`가 enabled 설치를 표시했으며 캐시된 `SKILL.md`의
SHA-256이 원본과 일치했습니다. `.codex-plugin/plugin.json`은 fixture에도 없었습니다.
실제 사용자 Codex 설치 목록에는 이 fixture가 나타나지 않았습니다. 이는 그 CLI의
Claude 형식 **메타데이터·파일 수용** 관측이지, 5-plugin 후보 설치, 자동 스킬 선택,
호스트 훅 동작이나 모델 응답 검증이 아닙니다. 후보를 marketplace에 등록하지 말라는
위 규칙은 그대로 유지합니다.

이후 **실제 2.11.7 후보의 플러그인 폴더 5개**를 별도 `CODEX_HOME`·`APPDATA`·
`LOCALAPPDATA`·임시 폴더를 지정한 Codex CLI 0.155.0에서 로컬 marketplace로
각각 등록하고 `plugin add`했습니다. `plugin list --json`은 5개 모두
`installed=true`, `enabled=true`로 반환했고, 캐시된 `SKILL.md` 182개의 SHA-256이
후보 원본과 전부 일치했습니다(7/61/22/32/60개). 테스트 홈은 release의
`diagnostics/codex-host-probe-20260927-0505/`이며 사용자 설치본은 전환하지
않았습니다. 여기서 허용한 것은 **격리 홈의 개별 plugin 폴더 등록**이지
`candidate/` envelope의 운영 marketplace 등록이나 사용자 프로필 설치가 아닙니다.
receipt 재검증은 동일 digest로 통과했지만 `installation_ready=false`입니다.
이 실측으로 확인한 범위는 Codex의 로컬 등록·복사·목록 조회뿐입니다. 자동 스킬
선택, 명시 명령 호출, hook 집행·차단, 모델 행동, 외부 의존 폐쇄성은 여전히 미검증이며
세 readiness flag를 올리지 않습니다.

### 레거시 `simonk-stack` 0.1.0 사용자 이전 (D-76 4단계)

카탈로그가 다섯 플러그인으로 바뀐 뒤(첫 `dist` 게시 이후)에 해당합니다. 4단계 호스트
실측(격리 설정 폴더, 레거시 0.1.0 설치 → 새 카탈로그 → `plugin update`)에서 확인한 사실:

- `plugin update simonk-stack@simonk-stack`은 같은 ID를 새 SimonKStack으로 **제자리
  교체**합니다(`updated from 0.1.0 to …`, 설치 항목은 1개라 중복이 생기지 않음).
- 나머지 넷은 설치되지 않습니다. 카탈로그만 갱신된 상태에서도 available 목록에만 뜹니다.
- 레거시 스킬 68개 중 58개는 새 SimonKStack에 있고, **10개는 사라집니다**: SimonKMarket으로
  옮긴 9개(`ad-monetization`·`analytics-integrator`·`global-payment-planner`·`growth-engine`·
  `payment-integrator`·`revenue-scenario-tester`·`store-launcher`·
  `subscription-manager-selector`·`tag-manager-integrator`)와 SimonKDesign으로 옮긴
  `consistency-guard` 1개입니다.
- plugin.json의 `dependencies`는 새로 `plugin install`할 때만 따라 설치되고 `plugin update`
  에서는 동작하지 않았습니다. 세션 시작 때 처리되는지는 확인하지 않았습니다.

그래서 업데이트한 사용자는 네 개를 직접 설치합니다(세션 안에서는 같은 ID로
`/plugin install <id>` 후 `/reload-plugins`):

```text
claude plugin install simonk-core@simonk-stack
claude plugin install simonk-market@simonk-stack
claude plugin install simonk-design@simonk-stack
claude plugin install simonk-aihub@simonk-stack
```

다섯 개 확인(5줄이 나오면 정상). PowerShell 5.1·7에서 4단계 `plugin list --json` 기록으로
동작을 확인했습니다:

```powershell
(claude plugin list --json | Out-String | ConvertFrom-Json) | Where-Object id -like 'simonk-*@simonk-stack' | Select-Object id, version, enabled
```

POSIX 셸: `claude plugin list --json | grep -o 'simonk-[a-z]*@simonk-stack'`

같은 안내를 빌드가 SimonKStack plugin.json description(`claude plugin details`에 보이는 줄)
끝에 덧붙입니다. README의 이전 절도 같은 명령을 씁니다.

### 비Windows 안전 훅 — 인터프리터 가드 (D-76 4단계)

**결함.** v2 safety projection은 careful·freeze·guard·investigate 훅을 exec form
`command: "python"` + `args: ["-B", "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py",
"check", <kind>, "--project", "${CLAUDE_PROJECT_DIR}"]`로 바꿉니다. `python`이 없는 호스트
(Ubuntu 26.04 기본은 `python3`만 있음)에서는 이 훅이 시작조차 못 합니다. Claude Code는
시작하지 못한 훅을 비차단 오류로 처리하므로 도구 호출이 그대로 실행됐습니다(fail-open).
`python3`로 돌리면 런타임이 비Windows에서 deny하지만 사유가 "Python·Git Bash를 고쳐라"였고,
freeze deny에는 빠져나갈 길이 없었습니다.

**공식 문서 근거** ([Hooks reference](https://code.claude.com/docs/en/hooks), 2026-10-04 열람):

- Exec form: "Claude Code resolves `command` as an executable on `PATH` and spawns it
  directly with `args` as the argument vector. There is no shell".
- Shell form: "The `command` string is passed to a shell: `sh -c` on macOS and Linux,
  Git Bash on Windows, or PowerShell when Git Bash isn't installed."
- 시작 실패: "A hook that can't start lands in the same non-blocking bucket. … For most
  hook events, the action proceeds."
- 차단: "Exit 2 means a blocking error" · 다른 종료 코드는 "doesn't block on its own" ·
  여러 훅은 "All matching hooks run in parallel" · "precedence is `deny` > `defer` > `ask` > `allow`".
- 세션 안 `/plugin disable <plugin>`은 Claude Code 2.1.289 도움말에, 셸의
  `claude plugin disable <id>`는 [Discover plugins](https://code.claude.com/docs/en/discover-plugins)에 있습니다.

**수정(방식 선택).** exec form 훅은 그대로 두고(Windows의 판정 경로 불변), 같은 matcher에
shell form **인터프리터 가드** 훅을 하나 더 붙입니다(`plugin_bundle.interpreter_guard`).
가드는 sh 내장 명령만 쓰고 경로 자리표시자가 없어서, 가드 자신이 필요로 하는 것이 빠질 수
없습니다.

- Windows 아닌 곳(`sh -c`): 항상 JSON deny + exit 2. 런타임이 Windows 전용이라 인터프리터가
  있어도 결과가 같고, 런타임도 같은 사유로 deny합니다.
- Windows(Git Bash): `python -c 'import sys; sys.exit(sys.version_info < (3, 7))'`가 성공하면
  exit 0으로 아무 판정도 내지 않습니다. 실패하면(없음·Store 가짜 `python.exe`·3.7 미만)
  런타임의 기존 fail-closed 사유로 deny + exit 2.

검토한 다른 길: (1) 전부 shell form으로 바꾸고 `python3`→`python` 순서로 찾기 — Windows가
Git Bash 경유로 바뀌고 Windows의 `python3`는 Store 별칭일 수 있어 Windows 동작이 달라집니다.
(2) 플러그인에 POSIX 런처 파일을 넣기 — exec form은 Windows에서 진짜 `.exe`만 실행하므로
Windows와 함께 쓸 단일 명령이 없고, 런처 파일이 빠지면 다시 시작 실패(fail-open)가 됩니다.
(3) 맨이름 `bash` 실행 — PowerShell에서 WSL `bash.exe`로 갈 수 있어 쓰지 않습니다.

**실측**(2026-10-04 23:2x~23:39 KST). 투영된 SKILL.md 프런트매터를 YAML로 읽어 각 훅을
문서 규칙대로 실행했습니다. exec form은 자식 PATH로 실행 파일을 찾아 셸 없이 띄웠고
(Windows는 node `child_process.spawn`, WSL은 PATH 검색), shell form은 Windows Git Bash
`bash.exe -c`, WSL `/bin/sh -c`입니다. 판정은 위 문서 규칙(exit 2·JSON deny 차단, 시작 실패·
기타 종료는 비차단, deny 우선)으로 합쳤습니다. 하네스: 세션 스크래치패드 `d76fix/measure.py`.
비교 대상 `main`은 origin/main의 투영 훅(같은 새 런타임 파일)입니다.

| 호스트·경우 | 페이로드 | main 훅 | 이 수정 |
| --- | --- | --- | --- |
| Windows, Python 3.12 | careful `git status` / `rm -rf /` | 통과 / deny(HIGH) | 통과 / deny(HIGH), 가드 exit 0 |
| Windows, Python 3.12 | freeze 경계 안 / 밖 Edit | 통과 / deny | 통과 / deny, 가드 exit 0 |
| Windows, PATH에 python 없음 | 네 페이로드 모두 | **통과(시작 실패 ENOENT)** | deny(RUNTIME FAILURE·freeze unavailable), 가드 exit 2 |
| Windows, 작동하는 Store 별칭 `python.exe` | 네 페이로드 | 위 Python 3.12와 같음 | 같음(가드 exit 0) |
| Windows, 작동 안 하는 `python.exe`(Store 가짜 대용) | 네 페이로드 | **통과(exit 1 비차단)** | deny, 가드 exit 2 |
| WSL Ubuntu 26.04, python·python3 모두 없음 | 네 페이로드 | **통과(ENOENT)** | deny(WINDOWS ONLY), 가드 exit 2 |
| WSL, python3만 | 네 페이로드 | **통과(ENOENT)** | deny(WINDOWS ONLY), 가드 exit 2 |
| WSL, python·python3 둘 다 | 네 페이로드 | deny(런타임) | deny(가드 exit 2 + 런타임 JSON deny, 같은 사유) |

WSL에서 런타임을 `python3`로 직접 돌리면 세 정책 모두 새 사유로 deny(exit 0), `clear`는
exit 2(`safety runtime state update failed`)입니다. 즉 비Windows에서 `/unfreeze`는 상태를 지울
수 없고, 사유가 이를 밝힙니다.

**비Windows deny 사유**(런타임 `NON_WINDOWS_REASONS`와 가드가 바이트 단위로 같음, 테스트로 고정):

- careful·careful-powershell: `[careful][WINDOWS ONLY] The SimonK safety runtime supports
  Windows only, so on this OS every Bash and PowerShell command is blocked on purpose (fail
  closed). This is not a verdict on the command. Way out: start a new session without /careful
  and /guard, or run /plugin disable simonk-core@simonk-stack (for /careful) or /plugin disable
  simonk-stack@simonk-stack (for /guard) and then start a new session.`
- freeze: `[freeze][WINDOWS ONLY] The SimonK safety runtime supports Windows only, so on this OS
  every Edit and Write is blocked on purpose (fail closed). This is not a verdict on the edit.
  /unfreeze cannot lift it here: the boundary state it clears exists only on Windows. Way out:
  start a new session without /freeze, /guard and /investigate, or run /plugin disable
  simonk-stack@simonk-stack and then start a new session.`

Windows의 deny·ask 사유는 바꾸지 않았습니다. Windows에서 python이 없을 때 가드가 내는
사유도 런타임의 기존 RUNTIME FAILURE·`Safety runtime unavailable` 문구 그대로입니다.

**남은 한계.** Git Bash가 없는 Windows는 shell form을 PowerShell로 돌리므로 가드가 구문
오류(비차단)로 끝납니다. 이때 python이 있으면 런타임이 Git Bash를 못 찾아 deny하지만,
python도 없으면 막지 못합니다. 런타임 파일 자체가 빠진 손상 설치도 막지 못합니다. 실제
Claude Code 세션 안 훅 실행(모델 턴)은 측정하지 않았고, 위 실측은 문서에 적힌 실행 방식을
재현한 것입니다. `/plugin disable` 직후 이미 등록된 스킬 훅이 같은 세션에서 바로 빠지는지도
확인하지 않아 사유는 "새 세션 시작"까지 안내합니다.

### 후보 경로 경고 분류 (2026-09-27)

같은 2.11.7 후보의 182개 스킬을 기존 `skill-gen-agent` 검증기로 다시 검사한
결과 오류 0건, 경고 49건(`W007` 2·`W009` 15·`W013` 32)이었습니다.
`W009`는 아래처럼 **15개 경고 발생 위치**를 분류해야 합니다. 모두를 15개의
누락 파일로 세거나, 검증기 성공을 실행 준비 완료로 해석하지 않습니다.

| 분류 | W009 위치 | 확인된 상태 |
| --- | ---: | --- |
| AIHub `rag-builder` | 1 | 참조 대상 `../llm-eval/scripts/gate.mjs`가 같은 후보 플러그인에 존재. 검증기의 스킬-로컬 경로 해석에 따른 오탐. |
| Core `gcloud-helper`·`keepass-helper`·`stack-update` | 10 | 참조하는 모노레포 루트 스크립트는 현재 소스에 있지만 분리 후보의 Core plugin에는 없음. 특히 gcloud/KeePass 지침에 원본 PC 절대 경로가 남아 있어 독립 설치의 실행 폐쇄성을 증명하지 못함. |
| Market `mobile-attribution-integrator`·`referral-program-builder`·`unit-economics-modeler` | 4 | 참조하는 보조 파일 4개가 후보뿐 아니라 Market 원본 `main`에도 없음. |

Core의 설치·업그레이드·자격증명 보조 스크립트를 경고 제거 목적으로 무심코
후보에 복사하거나 실행하지 않습니다. 각 스킬의 독립 패키지 계약과 안전성을
수리·검증해야 합니다. Market 원본 변경도 별도 소유 브랜치 검토 전에는 하지
않습니다. 이 분류만으로 세 readiness flag를 올리지 않습니다.
Market의 4개 자산은 단순한 장식 파일이 아닙니다. `parse-install-referrer.ts`는
Android referrer 정규화 단계, `k-factor-queries.sql`은 추천 성과 계산,
`check-referral-integrity.sh`는 지급 원장 무결성 검증,
`UNIT_ECONOMICS.template.md`는 최종 분석 산출물의 입력입니다. 원본에 없는
내용을 임의로 존재한다고 가정하거나 해당 검증 단계를 통과로 표시하지 마세요.

후보의 정적 경로 재검사는 번들 digest를 먼저 검증한 뒤 실행합니다. 로컬
`scripts/candidate_path_audit.py`는 `SKILL.md`와 거기서 도달 가능한 Markdown
보조 문서의 백틱 파일 경로·단순 Markdown 링크를 검사합니다. 백틱의
`scripts/`·`templates/`·`references/`·`assets/`는 스킬 루트 기준,
Markdown 링크와 `../` 경로는 해당 문서 기준으로 해석합니다. 같은 플러그인
안의 형제 스킬 경로(`../llm-eval/...`)도 확인합니다. 2026-09-30
`281fc11` 안전 후보에서는 스킬 182개에서 도달한 Markdown 문서 264개와
명시적 정적 참조 189개를 확인했고 미해결 참조·비이식 명령은 0건이었습니다.
동일 후보의 Codex 일반 안전 subset은 `subset.json`·원본 오버레이 영수증을
함께 검증한 뒤 177스킬·258문서·188참조를 확인했고 미해결 참조·비이식
명령은 0건이었습니다. 두 쪽 모두 외부 Gstack 참조가 남아
`external_runtime_pending`입니다. Codex의 D-29 안전/종속 스킬 5개 제외는
의도된 차이이며, 이 수치나 공통 스킬 본문 일치가 행동·품질 동등성 증거는
아닙니다.
종료 1은 미해결 경로·비이식 명령 또는 외부 Gstack 런타임 참조의
**문맥 검토 필요**이지 파일 누락 확정이나 실행 실패 증명이 아닙니다.
정적 경로만 충족하고 외부 참조가 남으면 `external_runtime_pending`을 반환합니다.
동적 경로·일반 상대 링크 전체·이름만 적힌 스킬 호출·Claude 전용 명령·
절대 호스트 경로·import·서비스·
자격증명·hook 동작은 범위 밖이고 `runtime_closure_verified`는 항상 false입니다.
`unresolved`에 `possible_targets`가 있으면 같은 플러그인 안의 동일 파일명
후보를 최대 5개 제시한 것입니다. 상대경로가 실제로 작동한다는 증거가 아니며
`unresolved` 상태와 종료 코드를 바꾸지 않습니다. 플러그인 밖 파일은 제안하지 않습니다.
현재 후보에서는 AIHub `gate.mjs` 1곳과 Core `simonk.ps1` 2곳에 제안이 나옵니다.
Core의 `skills/simonk/scripts/simonk.ps1`은 패키지 전용 계획 진입점으로,
`gcloud-helper`·`keepass-helper`가 설명하는 자동 동작의 대체재로 확인되지
않았습니다. 세 위치 모두 수동 검토 대상으로 남습니다.

```powershell
python -B scripts/candidate_path_audit.py --package '<candidate>' --expected-digest '<bundle_digest>'
python -B scripts/candidate_path_audit.py --package-kind codex-subset --package '<codex_subset>' --expected-digest '<subset_digest>' --source-overlay '<codex_overlay>' --overlay-digest '<overlay_digest>'
```

Codex subset 모드는 출처 오버레이가 없거나 일치하지 않으면 스킬 본문 감사 전에 차단합니다.
두 명령 모두 외부 Gstack 참조가 남은 현재 후보에서는 종료 1을 반환하므로
JSON `status`·`unresolved`·`unportable_commands`를 함께 검토하세요.

2.11.7 후보 digest `a26903c3…ec6da` 실측에서는 182개 스킬의 정적 참조 150개를
대조하고, 중복 제거된 `unresolved` 11개를 보고했습니다. 이 중 AIHub의
`scripts/gate.mjs` 표기는 같은 스킬의 실제 명령 `../llm-eval/scripts/gate.mjs`와
연결되므로 독립 파일 누락으로 세지 않습니다. 나머지 Core/Market 항목도
원본·후보의 파일과 스킬 의도를 대조한 뒤 수정 범위를 정해야 합니다.

`model-router` 0.2.2 소스 문구 갱신 후 기존 후보를 덮어쓰지 않고
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.7-refresh-candidate/`에
새 v2 후보를 만들었습니다. source digest는
`7d4861068847989a6b8a69a9ff2f91b50a87bb5648b4541aa60c5b37ebaaa6c3`,
bundle digest는 `9108b83165f13100f72d19abf1d1c75dae651f0aab40c5a7304cc7957430a063`입니다.
source 137스킬/407파일과 bundle 5플러그인/182스킬/713파일의 build·별도 verify가
통과했고, bundle 회귀 테스트는 43/43 PASS였습니다. 별도 Codex CLI 0.155.0
테스트 홈에서 5개 installed/enabled, 후보↔캐시 **전체 713파일**의 누락·변경·추가
0건, `/vibe` inventory 182 records/0 issues를 확인했습니다. source↔bundle
coverage의 차이는 이제 안전 어댑터로 의도적으로 변환한 5스킬뿐입니다.
정적 경로 검사는 새 후보에서도 같은 150참조·11문맥 검토 항목을 반환합니다.
이 호스트 관측은 설치·파일탐색 증거이며 스킬 선택/호출·hook 집행·실제 모델
행동을 인증하지 않습니다. 세 readiness flag는 여전히 false이고 실제 사용자
설치·운영 marketplace 전환은 별도 게이트입니다.

같은 refresh 후보를 Claude Code 2.1.283의 `--bare` + 반복 `--plugin-dir`로
세션 한정 조회하면 `plugin list --json`에 5개 모두 `@inline`/`scope=session`/
`enabled=true`로 표시됩니다. 플러그인 경로를 주지 않은 `--bare` 기준 목록에는
SimonK가 0개입니다. `plugin details`의 187개 구성요소는 실제 `SKILL.md` 182개와
`commands/*.md` 5개를 합친 수와 정확히 일치합니다(8/63/23/33/60개).
이 모드의 Always-on 합계 **~24,877 tok**는 CLI의 예상치이며 앞서 기록한 일반
모드의 ~41,580 tok과 조건이 달라 절감률로 비교하지 않습니다. 실제 토큰 사용량도
아닙니다. `--bare`는 hook를 건너뛰므로 훅 로딩·집행 검증으로 확대하지 마세요.
모델 생성 호출이나 영구 플러그인 설치는 없었습니다.

### `/vibe` 2.11.8 구독 전용 비용 가드 후보 (2026-09-27)

기능 브랜치 `feat/skill-context-budget-260925`의 `f2b2f35`는 구독 경로를
USD 0으로 예약하기 전에 **정확한 LLM 모델의 구독 포함 여부**(Grok Bot은
Bot 사용량 포함 여부)와 초과 사용·API fallback 비활성화를 각각 긍정적으로
확인하도록 바꿨습니다. 기본 추가 과금 승인액 USD 0에서는 견적이 0이라고
주장하는 API/metered 경로도 거부합니다. `billing.verified=true` 하나로는
사용 승인이나 무과금 보증이 되지 않습니다. 관측기가 알 수 없는 값은 그대로
`null`로 남기므로, 이 변경은 실계정의 포함 사용량을 새로 증명하지 않습니다.

새 산출물은
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.8-subscription-guard-candidate/`
아래의 `source`·`candidate`이며 기존 2.11.7 후보를 덮어쓰지 않았습니다.
source digest는
`198f8ccd2a6de57df414b3704e583be1d69236178dcb07885bdad418f11e3b90`,
bundle digest는
`45fd469af453ccf014bf2b13ac83c3a59dc4bb41b36fa6e071caece4b0e7403c`입니다.
source 137스킬/407파일, bundle 5플러그인/182스킬/713파일의 build·별도
verify가 통과했습니다. 최종 코드의 `/vibe` 테스트 210개와 중앙 라우터 통합
테스트 8개가 통과했고, 릴리스·번들 테스트 81개도 통과했습니다.

Core 원본 `main`의 HEAD `c080bda`는 고정 입력 `4369136`의 조상이며,
고정 입력은 `fix/semantic-recall-metadata-260924`의 후속 수정 3건을 포함합니다.
원본 브랜치를 체크아웃·되돌리지 않고 `inputs/`에 5개 원본을 로컬 복제해 지정된
커밋을 detached 상태로 고정했습니다. 이 디렉터리는 후보 재현용 입력이며
사용자 설치본이 아닙니다. 새 후보의 정적 경로 감사는 150참조 중 앞 절과
동일한 미해결 항목 11개를 보고하며 종료 코드 1입니다. 따라서
`runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는
모두 `false`입니다. 실사용 설치·모델 호출·정식 머지·원격 push는 하지 않았습니다.

### `/vibe` 2.11.9 모델 결속 후보 (2026-09-27)

기능 브랜치 `23b785c`는 `billing.model_included=true`를 다른 모델에서 복사해
USD 0 구독 경로를 통과시킬 수 없도록 `billing.included_model`을 선택된
실제 모델 ID에 결속합니다. alias가 있으면 검증된 resolved model을 사용합니다.
기본 승인액 USD 0에서 API/metered 경로를 차단한 2.11.8 계약은 그대로입니다.
또한 준비 절차 테스트의 USD 0 fixture가 구독이 아닌 API 경로를 쓰던 기존
모순을 수정했습니다. 이 패치는 독립적인 billing 관측 시각이나 실제 계정의
모델 포함 여부를 증명하지 않습니다.

기존 2.11.8 후보는 유지하고
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.9-model-binding-candidate/`
에 새 `source`·`candidate`·고정 입력 `inputs`를 만들었습니다. source digest는
`61c82676a72dca622f921e05d436f47cfe784524b6f7d76342fffa19a4dac851`,
bundle digest는
`92537eb4cd9ac3735c8ffa4e83285d2bf10eedf454237e78bd4d650b6aa6b1a5`입니다.
source 137스킬/407파일, bundle 5플러그인/182스킬/713파일의 build·별도
verify가 통과했습니다. `/vibe` 테스트 211개, 준비 절차 90개, 중앙 라우터
통합 8개가 통과했습니다. 정적 경로 감사는 이전과 동일하게 150참조 중
11건 미해결(종료 코드 1)이며, 세 readiness flag는 모두 `false`입니다.
호스트 실사용 설치·모델 생성 호출·정식 머지·원격 push는 여전히 별도 게이트입니다.

### `/vibe` 2.11.10 본문 예산 후보 (2026-09-27)

기능 브랜치 `1d13d8e`는 `/vibe`의 실행 규칙과 생성 라우팅 표는 유지하고,
Git/설치 문서로 추적 가능한 과거 버전 기록 55줄만 `SKILL.md`에서 제거했습니다.
source 파일 크기는 32,900→28,707바이트, 스킬 검증기 기준 본문은
416→362줄입니다. 이전 `W007` 본문 길이 경고는 source와 패키지 양쪽에서
0건이며, validator 오류도 0건입니다. 이는 선택 후 본문 부담만 줄인 결과로,
호스트 초기 description 축약 경고·실제 토큰 사용량·모델 선택 정확도 개선을
증명하지 않습니다. sync 표 검사, `/vibe` 87개, 중앙 라우터 8개, 준비 절차
90개 테스트가 통과했습니다.

2.11.9 후보를 보존하고
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.10-body-budget-candidate/`
에 새 source·bundle 후보를 생성했습니다. source digest
`ab7db4645c420f804684083672b108ec4e6e2d91449f33425a3cd267a415e6c0`,
bundle digest
`1a3963396749266759a1ee36b64d07fea5a5eb548d1a3b5cf3465db55ab89411`의
별도 verify가 통과했습니다. 이 후보의 입력은 이전 2.11.9 후보의 깨끗한
고정 커밋 `inputs/`를 재사용해 원본·설치본을 변경하거나 불필요한 Git 저장소
복제본을 추가하지 않았습니다. 5플러그인/182스킬/713파일과 정적 참조
150건/미해결 11건은 이전과 같습니다. 세 readiness flag는 여전히 false입니다.

### Market 보조 자산 후보 — 설치·활성화 아님

SimonKMarket 원본의 별도 브랜치 `fix/market-missing-assets-260927`에서
Install Referrer 파서, 추천 무결성 스캔, K-factor 측정 SQL, 단위경제성 템플릿을
복구했습니다. `distribution/plugin-inputs.v1.json`은 검증한 Market 커밋
`257c2cde94891369307899dac95681a243aaee59`을 고정합니다. 이전 후보와
원본 `main`·사용자 설치본은 변경하지 않았습니다.

새 검증 후보는 `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.10-market-assets-candidate/`
의 `inputs/`와 `candidate-safety-v2/`에 있습니다. 기존 2.11.10 source digest
`ab7db4645c420f804684083672b108ec4e6e2d91449f33425a3cd267a415e6c0`를
재사용했으며, bundle digest는
`8d7ea761ac6de6e3a54fbb7d198087cc91e1ed6f861057b924c7e54d1958cb1c`입니다.
기존 후보와 같은 `five-plugin-candidate-safety-v2` 계약의 5개 plugin·182개 skill·
720개 파일에 대한 바이트 검증은 통과했습니다. 동일 폴더의 `candidate/`는 비교용
기본 v1 계약 후보이며, 안전 변환이 빠져 있으므로 후속 후보로 사용하지 않습니다.
정적 경로 감사의 미해결은
11건에서 7건으로 줄었지만 결과는 여전히 `incomplete`이고, 나머지 경로는
AIHub 1건·Core 6건입니다. 이 감사는 실제 실행·호스트 호환·설치 승인이 아닙니다.
Market의 로컬 검증은 32개 skill 품질 게이트와 새 회귀 테스트 9개가 통과했습니다.
SQL은 운영 DB나 별도 PostgreSQL 테스트 DB에서 실행하지 않았습니다.

격리된 Codex 호스트 실험에서는 기존 전역 `.agents/skills` 항목들이 후보 Core
skill과 중복되어, 설치한 Core 61개 중 초기 프롬프트에 보이는 항목이 27개뿐이고
`simonk-core:vibe`가 후보 대신 이전 전역 경로를 가리키는 현상이 확인됐습니다.
전역 스킬 162개를 일시적으로 정확한 경로별 설정으로 비활성화했을 때는 후보
`vibe`/`vibe-bot`이 보였으나, 이는 실제 사용자 프로필 변경이나 안전한 마이그레이션
방법의 검증이 아닙니다. 전역 스킬에 후보와 서로 다른 내용·전역 전용 스킬이 있어
일괄 비활성화는 하지 마세요. 설치 전 선택적 중복 정리와 실제 호스트 재검증이 필요합니다.

### Codex frontmatter 검사 범위

로컬 `skill-creator/scripts/quick_validate.py`의 허용 키 목록은 실제 Codex
로더와 동일하다는 증거가 아닙니다. 이 helper는 `version`, `author` 등의 확장
키를 거부합니다. 반면 YAML 구문 오류·필수 name/description 부재는 별도로
확인해야 합니다. 검사 도구·버전/해시·대상 candidate digest를 함께 기록하고,
helper의 FAIL을 곧바로 native 로딩 실패로, 기본 구조 PASS를 native 호환으로
바꿔 보고하지 마세요. 공용 소스의 키나 hooks를 통과 목적으로 삭제하지 않습니다.

plugin-only 스킬도 검사 대상입니다. `semantic-recall`의 잘못된 plain scalar는
Core의 별도 수정 브랜치에서 고쳤으며, `distribution/plugin-inputs.v1.json`은
그 정확한 commit을 가리킵니다. 공식 main·설치본의 자동 변경은 아닙니다.
후보의 실제 호스트 로딩, 명시호출 정책·hooks, runtime 의존성과 행동 검증은
여전히 별도 게이트입니다. OpenAI의
[스킬 문서](https://learn.chatgpt.com/docs/build-skills)와
[plugin 검사 오류](https://developers.openai.com/plugins/deploy/submission-errors)는
서로 다른 적용 범위이며, 공개 directory 제출 규칙 전체를 로컬 CLI 규칙으로
간주하지 않습니다.

### 선택적 v2 safety projection — 여전히 격리 후보

`build`에 `--safety-adapter`를 추가하면 v1 exact-copy 대신 명시적
`five-plugin-candidate-safety-v2` 계약을 사용합니다. 기본값과 기존 v1 검증은
바뀌지 않습니다. v2는 careful/freeze/guard/investigate/unfreeze의 SKILL과
investigate scope 참고문서, 총 6개 입력의 정해진 hook/setup 부분만 변환합니다.
원본 source 파일과 3개 Bash leaf는 수정하지 않습니다.

Core/Stack 각각의 `.simonk-runtime/`에 helper와 Python adapter를 포함합니다.
이들은 skill이 아니며 새 SKILL.md나 두 번째 plugin home을 만들지 않습니다.
receipt의 `safety_projection.originals`는 변환/복제 입력 10개의 원본 바이트를
보관하고, verifier는 source manifest의 hash/size와 대조한 뒤 고정 변환을
재실행합니다. 출력 hash만 새로 쓰거나 원본/복제 helper를 바꿔 통과시킬 수
없습니다. 단 공격자가 모든 입력을 교체하고 사용자가 새로운 digest를 승인하는
경우까지 인증하는 서명 체계는 아닙니다.

```text
python -B scripts/plugin_bundle.py build --source-package E:/staging/release-a --source-digest <digest> --plugin-parent E:/reviewed/SimonK-Plugins --inputs distribution/plugin-inputs.v1.json --output E:/staging/plugins-safety-candidate-a --safety-adapter
```

### 2026-09-27 인증·갱신 계약 보정

현재 입력 핀은 AIHub의 RAG gate 경로 수정 `e37f07bf`와 Core의 독립 실행
안전 계약 `6527e816`을 포함한다. `gcloud-helper`와 `keepass-helper`는 상태
진단만 제공하며 인증·금고 열기·시크릿 주입을 실행하지 않는다. `stack-update`는
저장소별 안전한 fast-forward만 다루고 vendor helper 호출이나 프로필 강제
재설치를 포함하지 않는다. `web-publisher`는 기존 인증 세션이나 사전에 준비된
환경변수만 사용한다. 이 변경은 기존 설치본을 자동으로 바꾸지 않는다.

원본 Core와 소스 오버레이는 별도 저장소이므로 두 커밋을 함께 고정한 새 격리
후보를 빌드·검증해야 한다. 품질 게이트의 eval dry-run은 케이스 구문 검사이며,
실제 모델 행동·호스트 설치 검증 또는 운영 적용 승인으로 간주하지 않는다.
Stack 입력 `dde60fb`은 후보에서 남았던 plugin-only 스킬 9개의 평가 케이스를
추가하고 기존 배열형 케이스 4개를 공통 스키마로 변환한다. `/skstack`도 `/vibe`의
하위 절차로 명시한다. 이전 격리 후보 `20260927-vibe-helper-closure-candidate/
candidate-safety-v2-normalized`의 digest는
`55770a53f1f0f5fb332fc987d497cccb5ef05154b65f02d4706fe384e7aa3d9c`다.
5 plugin/182 skill/729 file 바이트 검증, 평가 dry-run 182/182, 정적 파일 경로
143개 미해결 0, Claude strict manifest 5/5가 통과했다. 평가 dry-run은 실제
모델 행동 증명이 아니다.

이전 후보를 별도 Codex 홈과 Claude 설정 디렉터리에 개별 설치한 결과 양쪽 모두
5개 plugin이 enabled이고 각 캐시의 전체 729파일 SHA-256이 후보와 일치했다.
이 설치는 격리 테스트 프로필에만 적용했고 실제 사용자 홈은 변경하지 않았다.
`/vibe` 명시 루트 inventory도 182개를 충돌 없이 인식했다. Codex 기본 예산에서
짧은 격리 홈의 전역 중복 136개만 선택적으로 비활성화하면 초기 prompt에는
plugin skill 105개(Stack 0개),
전역 전체 비활성화 시에는 127개가 보였다. [공식 설정 참조](https://learn.chatgpt.com/docs/config-file/config-reference)의
`skills.max_context_tokens=10000`을 격리 명령 인자로 적용하면 긴 홈·중복
136개 비활성화 시 plugin skill 138개(Stack 16개), 짧은 홈·전역 전체 비활성화
시 182개 전부가 초기 목록에 표시됐다. 이는 모델 선택 행동·훅 실행 증거가
아니다. 사용자 전역 전용 스킬을 일괄 비활성화하지 말고, 실제 호스트의 선택·
명시 호출·훅 동작을 별도 검증해야 한다. 사용자 홈에는 적용하지 않았다. receipt의
`runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는
계속 false이며 운영 설치·main 머지의 근거가 아니다.

### `/vibe` 2.11.11 Grok 복구 안내 후보 (2026-09-27)

기능 브랜치 `3538b23`은 과거 Grok HOLD를 영구 금지처럼 보이게 하던 안내를
최신 쿼터·선택 모델의 구독 포함·초과 과금 차단 재확인 규칙으로 바꿨다. 실제
라우팅·결제 게이트를 완화하거나 모델을 실호출하지는 않았다. 이전의 사용량
100% 시나리오는 유지하고, 복구 보고만으로 새 호출을 시작하지 않는 평가
케이스를 추가했다. `vibe` 버전은 2.11.11이다.

새 불변 소스 패키지는 `20260927-vibe-helper-closure-candidate/source-v4-grok-recovery`,
digest `53be3aa8942dfdefac38d7ed2493e7b61ec77854632566caab5a33ea75afb4ed`다.
선택할 새 v2 안전 후보는 같은 부모의 `candidate-safety-v4-grok-recovery`, digest
`fb6900863fde6dad51ecda9e930050b330b4c1e1917eda098ddf8b5f1d55986d`다.
5 plugin/182 skill/729 file byte verify, 평가 dry-run 182/182, 정적 파일 경로
143개 미해결 0, Claude strict manifest 5/5가 통과했다. 별도 Claude·Codex
테스트 프로필에서 각각 5개 plugin enabled, 후보↔캐시 729파일 해시 일치,
Codex `/vibe` 명시 inventory 182개/문제 0건을 확인했다. 초기 목록·모델 선택·
실제 훅 실행·실계정 청구·운영 설치까지 증명한 결과는 아니다. 안전 adapter를
적용하지 않은 별도 v1 진단 후보(`candidate-safety-v3-grok-recovery`, 721파일)는
보존하되 설치 대상으로 사용하지 않는다. 새 영수증의 readiness 세 플래그도
모두 false다.

포장된 안전 런타임은 실제 후보 파일을 별도 임시 디렉터리로 복사하여 검증할 수
있다. `SIMONK_SAFETY_CANDIDATE_PLUGIN_ROOT`를 각각 후보의 `plugins/SimonKCore`,
`plugins/SimonKStack` 절대 경로로 지정하고 다음을 실행한다. 기본값(변수 미설정)은
소스 런타임을 검사한다. 2026-09-27에 기본·Core 후보·Stack 후보 각각 21/21
통과했다. 이 검사는 실제 Claude `PreToolUse` 활성화나 모델 호출을 하지 않는다.

```powershell
$env:SIMONK_SAFETY_CANDIDATE_PLUGIN_ROOT = 'E:\Coding Infra\Releases\SimonK-stack\20260927-vibe-helper-closure-candidate\candidate-safety-v4-grok-recovery\plugins\SimonKCore'
python -B -m unittest scripts.tests.test_safety_runtime
Remove-Item Env:SIMONK_SAFETY_CANDIDATE_PLUGIN_ROOT
```

Hook는 `python` + `args`의 exec-form을 사용합니다. 정상 설치된 실제 Python
실행 파일이 PATH에 있어야 하며, native host가 이를 기동하는지는 별도 확인입니다.
adapter는 검토한 Git Bash만 사용합니다. `SIMONK_SAFETY_BASH`로 지정할 수 있고,
Windows의 WSL `bash.exe`를 대체 runtime으로 추측하지 않습니다. 최상위 Python
기동 자체가 실패하면 adapter의 deny/ask도 실행될 수 없으므로 호스트 활성화는
이 후보만으로 승인되지 않습니다.
변경하지 않은 Bash leaf의 JSON 파서를 위해 `node.exe`도 PATH에서 사용할 수
있어야 합니다. 의존성을 자동 설치하거나 PATH·전역 환경을 수정하지 않습니다.

상태는 `SIMONK_SAFETY_STATE_ROOT` 또는 `%LOCALAPPDATA%/SimonK/safety-v1` 아래
canonical project + host session ID로 분리합니다. plugin DATA나 변경 가능한
hook cwd를 상태의 식별자로 쓰지 않습니다. session ID는 namespace이지 호출자
인증 수단이 아닙니다. freeze 상태 부재/손상/접근 오류는 deny이며, 명시적
unfreeze가 기록한 inactive tombstone만 허용합니다. 이는 원본 leaf의
absent-file 허용 동작을 바꾼 것이 아니라 새 adapter의 전처리 계약입니다.
단독 작성·동일 사용자 환경 전제이며 OS 보안 경계나 Bash 파일쓰기 차단이 아닙니다.

**검사 시간 예산(2026-10-04, `freeze` 0.2.2, 허브 D-62 후속 5)**: 한 번의
검사(cygpath 호출 전부와 leaf)가 `CHECK_TIMEOUT` 20초 하나를 나눠 쓴다. 이전에는
프로세스마다 5초였고(freeze 최악 프로세스 6개 × 5초 = 30초), PR #112 이후 시간
초과가 `deny`가 되면서 무거운 테스트를 동시에 돌릴 때 정상 명령이 막혔다. 이 PC
(Ryzen 5 7500F, 12스레드)에서 careful Bash·careful PowerShell·freeze 검사를 조건마다
각 30회 쟀다(측정용 복사본은 제한을 120초로 올려 분포가 잘리지 않게 했다).

| 조건 | leaf p50 | leaf p95 | leaf 최대 | 훅 명령 전체 최대(Python 기동 포함) | leaf 5초 초과 |
|---|---|---|---|---|---|
| 평상시(다른 세션 작업 중) | 0.74~1.56초 | 1.40~1.98초 | 4.42초 | 7.22초 | 0/90 |
| 테스트 2개 동시(`test_plugin_bundle`·`test_check_careful`) | 0.85~1.78초 | 1.71~2.86초 | 2.87초 | 4.65초 | 0/90 |
| 테스트 3개 동시(+`test_safety_runtime` 반복) | 0.81~2.05초 | 1.79~2.49초 | 2.50초 | 2.79초 | 0/90 |
| 테스트 6개 동시(위 3개 × 2) | 2.78~3.60초 | 4.94~10.25초 | 11.30초 | 14.70초 | 14/90 |

6개 동시 조건에서 함께 돌린 `test_safety_runtime`은 20회 중 12회 실패해 #112 때의
거짓 차단을 재현했다. 20초는 이 최댓값(14.70초)을 덮으면서 이전 최악(30초)보다
짧다. Claude Code 문서상 `PreToolUse` 명령 훅의 기본 제한은 600초이고 시간 초과된
훅은 도구 호출을 막지 않으므로(fail-open), 예산은 그보다 훨씬 짧아야 한다.
예산을 다 쓰면 `deny`이며 사유가 시간 초과임과 다시 시도해도 안전함을 밝힌다
(careful `[careful][RUNTIME TIMEOUT] …`, freeze `[freeze] Safety check timed out …`).
측정은 이 PC 한 대의 값이며 실제 호스트 훅 경유 지연은 재지 않았다.

Setup의 host 치환값은 shell 코드로 재해석하지 않고 quoted heredoc의 raw data로
전달합니다. 이 후보는 실제 존재하는 **한 줄 Windows 절대 경로**와 host session
ID만 허용합니다. 임의 여러 줄 텍스트나 heredoc 종료 구문을 붙여넣지 마세요.
shell이 먼저 해석한 뒤 Python으로 검사하는 것은 shell injection 방어가 아닙니다.
investigate 참고문서는 Read 시 치환을 가정하지 않고, SKILL 본문에서 이미 치환된
setup 명령을 참조합니다. synced skill이나 다른 호스트의 치환 동작은 인증하지 않습니다.

검증은 격리 state root/후보/fixture 안에서만 수행합니다. 실제 사용자 state,
프로필, 설치본을 이 예제로 자동 전환하지 마세요. 세 readiness 플래그는 v2에도
false이며 전체 의존성·호스트 정책·설치 준비 완료 주장은 아닙니다.
공식 계약: [Skills substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions),
[Hook exec form](https://code.claude.com/docs/en/hooks#exec-form-and-shell-form).

### `/vibe` 2.11.12 Antigravity 1.2.12 메타데이터 재검증 (2026-09-27)

설치된 `agy.exe` 1.2.12의 `-p '/usage' --output-format json`은 성공·0턴·
모든 토큰 카운터 0으로 실측했다. [공식 변경 기록](https://github.com/google-antigravity/antigravity-cli/blob/main/CHANGELOG.md)은
이 읽기 전용 명령이 모델 턴·쿼터를 쓰지 않는다고 설명한다. 수집기의 정확한 버전
허용 목록에 1.2.12만 추가했고, 회귀 테스트가 이전 미확인 버전 차단과 새 버전의
0턴 계약을 함께 검사한다. 실제 수집 결과는 Gemini 주간/5시간과 타사 주간/5시간
버킷 네 개를 반환했지만 계정 참조·과금 방식·모델 목록은 여전히 미확인이다.
이 관측은 생성·무료 모델 접근 허가가 아니다.

이 PC의 `agy models --output-format json`은 exit 1이며, 인자 없는 `agy models`만
텍스트 슬러그를 반환했다. 따라서 공식 변경 기록의 JSON 하위 명령 설명을 이
바이너리의 동작으로 간주하지 않고 모델 목록을 실행 후보에 편입하지 않았다.
기존 2.11.11 배포 후보는 불변으로 보존했다. 새 소스 패키지는
`20260927-vibe-helper-closure-candidate/source-v5-agy-1212`, digest
`b6d95f0008299a3df24aeb16f13454332c9958ab537199772d3b026fc6a2b347`이며
137 skill/407 file을 재검증했다. v2 안전 번들은 같은 부모의
`candidate-safety-v5-agy-1212`, digest
`ed02ba503feb835885a43563657677e272aac44bbfe5e6575d9f8060ae767ecc`다.
5 plugin/182 skill/729 file byte verify, 정적 경로 143개 미해결 0,
평가 dry-run·프로젝트 검사 182/182, Claude strict manifest 5/5,
Claude 세션 한정 로드 5개 enabled를 확인했다. 별도 Codex 진단 홈에서도
5개 enabled와 후보↔캐시 729파일 SHA-256 일치를 확인했다.
이 검증은 실제 모델 선택·훅 발화·개별 모델의 구독 포함을 증명하지 않으며
세 readiness 플래그는 계속 false다.

### `/vibe` 2.11.13 GUI 자연어 진입점 보강 (2026-09-27)

Claude Max `claude.ai` 로그인과 API 키 환경변수 부재, 사용자의 초과 사용 차단
확인 뒤, 도구를 전부 끈 격리 `claude -p` 1회를 실행했다. Play Console 상태
확인에 맞는 스킬을 묻자 존재하지 않는 GUI 전문 스킬을 답했다. 이는 슬래시
호출 없이 실제 선택을 증명하려던 제한된 평가의 실패이며, 플러그인 훅·봇
전달의 검증 결과가 아니다. CLI는 `total_cost_usd=0.222612`를 표시했다.
이 값은 CLI의 비용 표시 필드이며 실제 추가 청구 내역은 확인하지 못했다.
추가 생성 호출은 중단했다.

후속으로 `/vibe` frontmatter에 Play Console/GUI 자연어 트리거와
`CLI/API/MCP` 우선 확인, 실제 `vibe-bot` 이름을 앞부분에 넣고 가상 전문
스킬을 만들지 말라고 명시했다. 자동 선택 행동이 개선됐다는 주장은 하지
않는다. 구독 포함 경로와 초과 사용 차단은 실호출마다 재확인하며,
readiness 세 플래그는 계속 false다.

최종 격리 후보는 같은 릴리스 부모의 `source-v7-gui-routing`(digest
`128fc2716a71974197eb4325f4370915527663bda1298669d893fb19a6609384`,
137 skill/407 file)과 `candidate-safety-v7-gui-routing`(digest
`f9716627dd05973811dd81aa56454db4e5a8794ba663792d9503e0ae07903107`,
5 plugin/182 skill/729 file)이다. 두 영수증 검증, 후보 182개 평가 파일
dry-run·validator 182/182, 정적 경로 143개 미해결 0, Claude strict
manifest 5/5, Claude 세션 한정 플러그인 5개 enabled,
별도 Codex 검사 홈의 플러그인 5개 enabled·캐시 729파일 해시 일치,
`/vibe` 단위 213개와 소스 품질 141/141이 통과했다.
전체 배포 도구 단위 테스트는 장시간 미완료로 중단했으므로 통과로 기록하지 않는다.
2.11.13의 전반적인 모델 선택 정확도와 호스트 훅 실행도 미검증이다.

2026-09-27 후속 점검에서 위 `--tools ''` 평가는 `Skill` 사용도 막는
비대표 조건임을 확인했다. 따라서 가상 스킬 답변을 일반적인 자동 선택 실패
증거로, 2.11.13 설명 수정의 효과로 모두 해석하지 않는다. 같은 질문을
`--restricted --tools Skill --allowedTools Skill --permission-mode dontAsk`로
격리 실행하자 2.11.13 후보는 `vibe`, 설명 재작성 실험 후보는
`simonk-core:vibe`를 한 번씩 답했다. 두 실행 모두 파일·셸·웹 도구와
봇 전달은 없었고, 스킬 도구 호출 자체도 관측되지 않았다. 이는 단일
응답 표본일 뿐 반복 선택 정확도나 실제 스킬 본문 호출 증거가 아니다.
평가 케이스에는 질문을 추가했으며 설명 재작성은 되돌렸다. 새 후보를
만들더라도 이 증거만으로 readiness를 올리지 않는다.
평가 케이스 보강 후보 v9에 명시 `/vibe`를 같은 격리 조건으로 한 번
질의한 결과, 응답은 CLI/API/MCP 우선, GUI-only일 때 `vibe-bot`, 추가
과금 USD 0을 올바르게 설명했다. 관측된 `Skill` 도구 호출은 없으므로
자동 오케스트레이션의 종단 간 증거로 세지 않는다. 다만 명시적
`/스킬` 호출은 `Skill` 도구를 거치지 않고 확장될 수 있으므로,
도구 호출이 없었다는 사실만으로 스킬 본문 미로딩을 단정하지 않는다
(https://code.claude.com/docs/en/hooks#userpromptexpansion).
이와 별도로 v9 Core를 `--plugin-dir`로 로드한 Claude Code 2.1.283
격리 세션에서 `--restricted --tools Skill --allowedTools Skill`을 지정하고
`simonk-core:vibe` 로드를 요청했다. JSONL에는 실제 `Skill` 도구 호출
`{"skill":"simonk-core:vibe"}`와 본문의 첫 제목 두 개를 그대로
반환한 응답이 기록됐다. 이는 Claude의 **명시적 Skill 도구 로드 한 건**을
입증하지만 자연어 자동 선택 정확도, 하위 스킬 실행, 모델·effort 선택,
다른 호스트 또는 운영 설치를 입증하지 않는다. 파일·셸·웹 도구는 허용하지
않았고 `--no-session-persistence`를 사용했다. CLI `total_cost_usd`는
추정 사용량 표시이며 추가 청구 영수증으로 해석하지 않는다.

Anthropic의 2026-06-15 공식 업데이트는 현재 `claude -p`가 구독 사용량을
사용한다고 명시한다(https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
이전 CLI의 `total_cost_usd`는 실제 추가 청구 영수증이 아니며, 결제
설정이나 충전 설정은 변경하지 않았다.

평가 케이스만 보강한 새 불변 패키지는 `source-v9-eval-protocol`
(digest `1708dbb6b8ba774a6acd0240dc04392d85b02e603518dc93c44b7fce251de92d`,
137 skill/407 file)과 `candidate-safety-v9-eval-protocol`
(digest `f94533fd4b7556c1298984ede0bc93f2af7c17f168186cb19dbced34d1095adb`,
5 plugin/182 skill/729 file)이다. 두 영수증 재검증, 정적 경로 143개
미해결 0, `/vibe` 단위 213개를 확인했다. 설치·호스트 호환·런타임 closure
플래그는 모두 false이며 v7 운영 후보를 대체 설치하지 않았다.
Claude `plugin details`로 v9 Core·Stack을 확인하면 둘 다 `Hooks (0)`이다.
이는 plugin-wide 훅 수이며 SKILL.md frontmatter의 세션 훅 수가 아니다.
Claude 공식 문서는 스킬 호출 시 frontmatter 훅을 등록한다고 명시한다
(https://code.claude.com/docs/en/hooks). 따라서 이 숫자로 스킬 훅의
미등록을 단정할 수 없다. 별도 격리 Claude Max 호스트 테스트에서
`/simonk-core:careful` 호출 후 무해한 `printf` 문자열에 포함된
`DROP TABLE demo`가 실제 PreToolUse에서 `SQL DROP detected`로
가로채졌고, `dontAsk` 세션은 명령을 실행하지 않았다. 같은 명령에 대한
후보 helper의 오프라인 판정도 `ask`였다. 디버그 로그는 릴리스 부모의
`diagnostics/hook-skill-probe-260927/`에 있다. 이 첫 검사는 해당 버전·
호스트의 Core `careful` Bash 훅 한 건만 입증한다. Stack `freeze`의
별도 후속 결과는 아래와 같으며, `guard`, 훅의 전체 수명주기,
Codex/Antigravity/Grok 또는 운영 설치 호환성은 여전히 미검증이다.

같은 v9 Stack 후보를 Claude Code 2.1.283의 별도 격리 세션에서
`Skill {"skill":"simonk-stack:freeze"}`로 호출했다. 경계를 설정하지 않은
새 세션의 `Write`는 `Safety runtime unavailable; blocked, fail closed`로
거부되고 대상 파일은 생성되지 않았다. 이어 다른 새 세션에서 상태 루트를
릴리스 진단 폴더로 격리하고 문서화된 setup launcher로 기존 `allow/`
경계를 설정했다. 바깥 `outside.txt`의 `Write`는 PreToolUse에서 차단되어
파일이 없고, 안쪽 `allow/inside.txt`의 `Write`만 성공해 정확한 테스트
문자열을 담았다. 상태 파일 한 개의 active 경계도 `allow/`와 일치했다.
이는 **해당 PC·Claude Code 버전·Stack freeze의 Write 경계 한 건**이며
Edit 매처, unfreeze/세션 종료 정리, 다른 호스트나 사용자 설치본 증거는
아니다. 테스트 파일과 상태는 `diagnostics/hook-skill-probe-260927/`에
보존했고 실제 사용자 safety state·설정은 수정하지 않았다.

2026-09-27 추가 검증에서 `scripts/tests`의 10개 테스트 파일을 각각
완료까지 실행해 합계 **247/247 PASS**를 확인했다(릴리스 38, 번들 43,
안전 훅/런타임 49, 설치 프로필 15, 진입점 26, 멀티터미널 21,
벤치마크 19, 선택 평가 26, 후보 경로 10). 별도
`scripts/test_model_router_integration.py`는 **8/8 PASS**,
`skills-src/vibe/scripts`의 테스트는 **213/213 PASS**다. 이전의
장시간 중단 기록은 그 당시 실행 결과이며 이 분할 실행으로 해당
테스트 파일들의 완료 상태가 갱신됐다. 실제 CLI 실발송, 전체 호스트
수명주기, 사용자 설치·과금 청구 검증으로 확대 해석하지 않는다.

## 보관된 설치 기록

오래된 기록은 기간별 파일로 옮겼다. 내용은 바꾸지 않았다(2026-10-04, Simon 지침 §0-1의 400KB 기간 분할).

- [`install/INSTALL-2026H2.md`](install/INSTALL-2026H2.md) — 2026-09-27 ~ 2026-09-30: frontier 메타데이터·구독 평가 경계, `/vibe` 2.11.15 v14 ~ 2.12.24 정적 격리 후보, v19 ~ v31b, Antigravity `/usage` 계약, D-33 릴리스 펜스

위 "공식 5-plugin 배포 후보" 절 안의 2026-09-27 하위 기록은 절차 설명과 섞여 있어 이 문서에 남겼다.

## `/vibe` 2.12.24 게시·재계획 보정 후보 (2026-10-01)

독립 PR 검토에서 플래너의 정확한 Bot 상태 검사와 게시 어댑터의 접두어
검사 불일치를 확인했다. 현재 `vibe-bot/bots.json`의 `active - reported ...
live access unverified`는 실행 권한이 아닌 과거 스냅샷이며, 이제 Bot·Relay
양쪽 게시 게이트에서 정확한 `active`만 인정한다. 또 실행을 바꾸지 않는
`shadow_task_fit` 권고의 만료/순위 변화는 불변 작업 의도와 Orca Task
본문에서 제외해 정상적인 `Store.refresh`를 허용한다. 두 회귀는 수정 전
각각 실패했고 수정 후 Bot 38건·`/vibe` 302건·저장소 공통 390건
(3건 조건부 skip)과 스킬 품질 141/141이 통과했다.

`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-bot-gate-fix/`의 네
영수증은 별도 verify 종료 0이다. `source/release.json` =
`044c466e27a3ae08fd09d6d45a92d29a9b01107ddc1180c746cb80283186598f`,
`candidate-safety/bundle.json` =
`410a0e0e7e7d7c206cf227295a410062215f9ae65872cfe104c6c48769851189`,
`codex-overlay-safety/overlay.json` =
`728a50460ef59a84a2d251a43956f100e7b8ff40d7425ecab46044f2eb045133`,
`codex-subset-safety/subset.json` =
`e24a9dcfa4608d209de7d4725a8fce28e9b190780495001497edcb2c343bfb1a`.
Claude 182/Codex 177, 공통 스킬 본문 176개·payload 617파일은 바이트가
같고 일회용 오프라인 probe 네 단계가 통과했다. 정적 경로 누락·비이식
명령은 각 0건이나 Gstack 외부 런타임은 각각 31·30스킬의
`external_runtime_pending`으로 남는다.

이 후보의 소스 420파일은 PR #63의 보정 당시 HEAD
`c8245ef8a275eca19dc0fab73677a84a69f31472` Git archive와 전부
SHA-256 일치한다. 해당 HEAD의 PR/branch CI 6개 검사와 Cloudflare Pages
preview check도 success다. 서로 다른 네트워크·클립보드 차단 Sandbox 두 곳에서
Claude Code 2.1.285는 플러그인 5개·182스킬·사용자 중복/디버그 오류 0,
Codex CLI 0.159.0은 플러그인 5개 enabled를 확인했다. 두 호스트 모두
이전 링크 5+2개를 두 번 복원하고 설치 플러그인을 0개로 철회했다.
증거는 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-bot-gate-host-rehearsal/output/`
의 `integrated-result.json`, `codex-integrated-result.json`에 보존했다.
모델/이미지/Bot 실호출이나 실제 사용자 홈 변경은 없었다.

이 격리 설치·복원은 Gstack 외부 런타임, 자동 스킬 선택·실효 effort·결과
품질, 실제 사용자 홈 백업·복구, 구독 포함 과금을 입증하지 않는다.
`installation_ready=false`와 `host_compatibility_verified=false`를 유지한다.
Cloudflare 운영 자동 배포는 Simon이 이번 `main` 머지에 한해 허용했지만,
독립 수정 재검토와 소스 전용 머지 결정 기록은 여전히 필요하다.

2026-10-01 **PR #65–#67 소스 HEAD 격리 후보**: `8798774a946e16aac17a0721fbff76b8fd1a2cc9`
소스에서 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-current-candidate/`
아래 새 후보를 만들었다. 입력은 `distribution/plugin-inputs.v1.json`에 고정된
5개 커밋의 깨끗한 별도 로컬 복제본이며, 원본 플러그인과 사용자 설치본은 바꾸지 않았다.

| 산출물 | 검증한 전체 digest | 범위 |
|---|---|---|
| `source` | `a8d9613b5286d916dfd3c3e591a81288abec148157dead599b6c30397aa8ac69` | 137스킬·423파일 |
| `candidate-safety` | `421d0f98666f05aacee9c66dcc47d430374aed4af0358000e529b75694f92fcc` | 5플러그인·Claude 182스킬 |
| `codex-overlay-safety` | `8262450952e45e7f3b2ea34eae421f892a788cf23943be0889ade13fe7c26737` | Codex 호환 오버레이 |
| `codex-subset-safety` | `8c918ac9b3a3bb406edba4b2b09bf5a0b23b01ce0ff79a609ba9293a162eb44e` | Codex 안전 부분집합 177스킬 |

네 영수증의 별도 `verify`가 모두 종료 0이고, Claude 후보의 일회용
`candidate_runtime_probe.py` 네 단계(`/vibe` selftest·runtime·prepare·table-sync)도
모두 종료 0이다. `preview-vibe-candidate.ps1 -AllPlugins` 기본 CheckOnly는
5개 플러그인·182스킬을 확인하고 `model_called=false`로 종료 0이었다.
정적 경로 감사에서 누락·비이식 명령은 양쪽 모두 0건이지만, Gstack 외부
런타임 힌트는 Claude 31스킬·Codex 30스킬로 남아 감사 종료 코드는 1이다.
이 후보는 실제 호스트 설치·자동 선택·이미지/Bot/모델 실호출이나 추가 과금
차단을 증명하지 않는다. `installation_ready=false`와
`host_compatibility_verified=false`를 유지하며, PR #65–#67의 새 §35 토론
D-code와 정확한 머지 대상 재검토 전에는 `main` 머지하지 않는다.

같은 후보의 격리 호스트 시험은
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-host-rehearsal/`에
원시 결과와 시험 설정을 보존했다. 소스 영수증 423파일은 문서만 추가된 HEAD
`a1d84b7b8f76336207b7a50b655cea812acc8138`의 Git archive와 전부 SHA-256
일치했다(누락·불일치 각 0). 별도 Windows Sandbox 두 개는 네트워크·클립보드·
장치 리디렉션을 끄고 후보와 실행 파일을 읽기 전용으로 매핑했으며 사용자 홈·
자격증명은 매핑하지 않았다. Windows Sandbox CLI로 각 게스트를 기동하고
준비한 스크립트를 System 컨텍스트에서 1회 실행했다. 첫 GUI 클라이언트
기동은 5분 이상 게스트 ID·결과가 없어 미완료로 기록하고 해당 클라이언트만
종료한 뒤 CLI 경로로 재시험했다.

Claude Code 2.1.285의 `integrated-result.json`은 플러그인 5개·스킬 182개,
사용자 중복·디버그 오류 0, 기존 링크 Claude 5개/Codex 2개 두 번 복원,
시험 플러그인 최종 0개로 `guest_integrated_marketplace_split_passed`다.
Codex CLI 0.159.0의 `codex-integrated-result.json`은 5개 플러그인 모두
활성, 별도 링크 전환 후 같은 복원·철회로
`guest_codex_plugin_alias_coexistence_passed`다. 두 결과 모두 인증 환경변수
없음·활성 네트워크 어댑터 0·모델 생성 미실행을 기록한다. 종료한 두 게스트의
`wsb.exe list --raw`에는 남은 인스턴스가 0개였고, 시험 전후 후보 영수증
SHA-256은 변하지 않았다. 원시 결과 SHA-256은 Claude
`455a7089ccde5d4e56cceb34a1984326d4120ddfcb6ab6da6d31cadaa4a1db78`,
Codex `1b45ae6c0a9ad491f5c87e64a1c9eb8323aeeda271f0ac1174794134b41a94cb`다.
이는 빈 게스트의 호스트 적재·복원 증거이지
Codex 177스킬의 실제 선택·전체 실행이나 사용자 홈 무손실 이관은 아니다.
Gstack 외부 런타임·모델/effort 선택 품질·이미지/Bot 실제 작업·구독 청구
경로는 여전히 미검증이므로 readiness 플래그는 `false`다.

## PR #67 툴링 옵션 안전성 수정 후보 (2026-10-01)

`9bd305f`에서 `check_tooling.py --help` 또는 알 수 없는 옵션이 전체
점검으로 빠져 npm 원격 조회와 기존 Orca `skills list`를 실행하던 경로를
차단했다. `--help`/`-h`는 도움말만 출력하고, 알 수 없는 옵션은 종료 2로
실패한다. 인자 없는 호출과 `--json`은 여전히 전체 점검이므로 운영 Orca
격리 조건에서는 호출하지 않는다. 수정 전 재현 테스트 3개 실패, 수정 후
`test_check_tooling.py` 11개·`/vibe` 스크립트 테스트 320개 통과,
`validate_skill.py skills-src/vibe` 0오류·0경고였다.

새 격리 후보는 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-help-safe-candidate/`
에 있다. 기존 후보와 사용자 홈은 바꾸지 않았다. 고정된 다섯 플러그인
커밋을 독립 로컬 복제본(`inputs-lf/`, Git 자동 CRLF 변환 OFF)으로 읽었고,
실패한 초기 입력(`inputs/`)은 후보 payload가 아니다.

| 산출물 | 전체 digest | 검증 범위 |
|---|---|---|
| `source` | `84083a33a2c61e3f7ec7a10ca5c25a290132ecc74d718a26ef369da338159854` | 소스 소유 137스킬·423파일, verify 0 |
| `candidate-safety` | `428233bb651658a81d145413df34d2275f8ed5646a6c7ca38a0babdf5f68c4c5` | Claude 5플러그인·182스킬, verify 0 |
| `codex-overlay-safety` | `e5139b761e4e97498d638b91b5ea0fd1d9c8951d4370dd49527f9b3a00890ec1` | Codex 호환 오버레이, verify 0 |
| `codex-subset-safety` | `83c32157ccf3ef5f793404abc1ededf2328df7b0de32b75316e05e5c10f51732` | Codex 안전 부분집합 177스킬, verify 0 |

Claude 후보의 격리 복사에서 오프라인 `/vibe` probe 4/4가 통과했고,
5플러그인 CheckOnly는 `model_called=false`였다. 정적 경로 감사의 누락·
비이식 명령은 두 호스트 모두 0건이지만 Gstack 외부 런타임 힌트가
Claude 31/Codex 30스킬에 남아 두 감사 모두 `external_runtime_pending`
(종료 1)이다. 문서·CI만 더한 `b0a7400`에서 소스 패키지를 다시 빌드해
423파일의 전체 digest가 위 `source`와 정확히 같음을 확인했다.

이 정확한 후보의 호스트 리허설은
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-help-host-rehearsal/`
에 보존했다. 별도 Windows Sandbox 두 개에서 네트워크·클립보드·장치
리디렉션을 끄고 사용자 홈·인증정보를 매핑하지 않았다. Claude Code
2.1.285는 5플러그인·182스킬 적재, 중복·디버그 오류 0, 이전 링크
Claude 5/Codex 2개 두 번 복원, 시험 플러그인 최종 0개로 통과했다.
Codex CLI 0.159.0은 5플러그인 활성 등록과 같은 링크 복원·철회로
통과했다. 두 게스트 모두 `no_auth_env=true`, 네트워크 어댑터 0,
`model_generation_executed=false`였고 종료 뒤 `wsb.exe list --raw`는
남은 인스턴스 0개였다. 원시 결과 SHA-256은 Claude
`25a13b38b1b66ffdbaa29e3726ec1b626f481abbb3724dba47287aa12fe75e18`,
Codex `8a94db308f152d6c1d1a5fb306b1af7a7e50d68c40d38d7a370add8e2d5c3d2a`다.
이는 빈 게스트의 적재·복원 시험이다. 모델/effort 자동 선택 품질,
전체 스킬 행동, Gstack 외부 런타임, 구독 청구 경로, 실제 사용자 홈 이관은
검증하지 않았으므로 `installation_ready=false`,
`host_compatibility_verified=false`, `runtime_closure_verified=false`를
유지한다. 모델·이미지·Bot 생성, 운영 Orca 조회, 사용자 홈 설치는
이 후보 검증에서 실행하지 않았다.

## PR #65–#67 재검토 후보 (2026-10-01)

독립 리뷰의 이미지 quota 바인딩·terminal 불변성·Codex 산출물 private
경계·Grok collector CI 네 지적을 수정했다. 추가 리뷰의 성공 후 거절된
이미지 재진입 오류도 재현 테스트로 고쳤다. #65 `cf86d14` → #66
`8c6d1aa` → #67 `25863bc` 순서로 통합했고, 이 정확한 #67 소스에서
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-reviewed-candidate/`
를 새로 빌드했다. 이전 후보와 사용자 홈은 보존했다.

| 산출물 | 전체 digest | 오프라인 결과 |
|---|---|---|
| `source-final` | `d598124cd41ebaed62d24b401c557f1f129b59f9cb3d6c39f20e456142f804d8` | 137스킬·423파일, verify 0 |
| `candidate-safety` | `f79e24ba7f32d217a3372182468fa071735bf52a95e4e7202f59e75d633dd950` | Claude 5플러그인·182스킬, verify 0 |
| `codex-overlay-safety` | `2654446c832dd4f162caac53cb073d184a7a1e74586143e1152c6aca5e030ee5` | Codex 변환, verify 0 |
| `codex-subset-safety` | `3bf17ba8a2b181f7cc8d07149cbe497ac5b827f12057908c623270ec77bde433` | Codex 177스킬, verify 0 |

최종 `/vibe` 스크립트 테스트 322개, 스킬 quality 141/141, 오프라인 후보
probe 4/4가 통과했다. 정적 경로 감사는 Claude/Codex 모두 누락·비이식
명령 0이지만 Gstack 외부 런타임 힌트가 각각 31/30스킬에 남아
`external_runtime_pending`(종료 1)이다. 이는 통과 판정이 아니다.

정확한 후보의 무인증 Windows Sandbox 리허설은
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr67-reviewed-host-rehearsal/`
에 보존했다. 네트워크·클립보드·장치 리디렉션을 끄고 사용자 홈·인증정보를
매핑하지 않았다. Claude Code 2.1.285는 5플러그인·182스킬 적재,
디버그 오류 0, 이전 링크 Claude 5/Codex 2개 두 번 복원을 확인했다.
Codex CLI 0.159.0은 5플러그인 활성 등록 및 같은 복원을 확인했다.
두 게스트 모두 `no_auth_env=true`, 네트워크 어댑터 0,
`model_generation_executed=false`였고 종료 후 `wsb.exe list --raw`에
남은 인스턴스는 0개였다. 원시 결과 SHA-256은 Claude
`f3aca9f0d00b5d06461dc6895972ab48c7997568d26125e64b31a373ea404b25`,
Codex `c04a86133e10ec35609b0df1fef49dd24aa74f77cf9ac4709382ca119d7ee430`이다.
이 결과는 적재·복원만 검증한다. 실제 선택·이미지 생성·Grok Bot 배달·
Gstack 실행·청구 경로·사용자 설치는 미검증으로
`runtime_closure_verified=false`, `host_compatibility_verified=false`,
`installation_ready=false`를 유지한다.

## PR #69 크레딧 누락 차단 후보 (2026-10-01)

실제 Codex 계정의 읽기 전용 한도 메타데이터에서 사용 가능한 구매 크레딧이
관측됐다. 실제 청구가 발생했다는 뜻은 아니다. 구독 포함 사용량 소진 뒤
기존 크레딧이 사용될 수 있으므로 모델 실호출은 보류한다. 코드 검토 중에는
`credits` 필드가 완전히 빠진 계획·최종 CLI 관측값을 안전하다고 통과시키는
별도 결손도 찾았다. 누락·빈 버킷 회귀 테스트가 수정 전 실패했고, 지금은
크레딧 상태가 하나도 확인되지 않으면 `PAID_CREDIT_EXPOSURE`로 차단한다.

새 후보 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-missing-credit-guard-candidate/`
는 고정된 다섯 원본 커밋을 LF 줄바꿈의 별도 로컬 복제본에서 읽었다.
원본 저장소와 기존 후보·사용자 홈은 변경하지 않았다. 네 영수증의 바이트
검증과 오프라인 probe 4/4가 통과했다.

| 산출물 | 전체 digest | 검증 범위 |
|---|---|---|
| `source` | `6750801afdddfa9d5b74a02b4644b8eb1968dabd62dd92933168d7722f305e64` | 137스킬·423파일 |
| `candidate-safety` | `0091dda445f6a753a5366d855ef6eb941828082f56787e7b150f4a3b371a8ad7` | Claude 5플러그인·182스킬 |
| `codex-overlay-safety` | `9bc995533c9acfd6b9dff83c88b2f6dc3b2d39c095636b5fff69eec37768637c` | Codex 호환 투영 |
| `codex-subset-safety` | `80e2c7e2cc201d725045399612f9947f959fc8a6e7cc9ba833b3557154b22fc1` | Codex 177스킬·출처 검증 |

`/vibe` 단위 테스트 327건, 자체 점검 180항목, Bot 자체 점검 93항목,
스킬 품질 141/141이 통과했다. 정확한 새 후보는 별도 Windows Sandbox
두 곳에서 네트워크·클립보드·장치 리디렉션과 인증정보 없이 적재·복원을
재실행했다. 결과는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-missing-credit-host-rehearsal/`
에 보존했다. Claude Code 2.1.285는 플러그인 스킬 182개·디버그 오류 0,
고정 Codex CLI 0.155.0은 플러그인 5개 활성, 양쪽 모두 기존 링크
Claude 5개·Codex 2개를 두 번 복원하고 시험 플러그인 최종 0개였다.
두 게스트의 인증 환경변수·활성 네트워크·모델 생성은 0이고 종료 뒤
Sandbox 실행 인스턴스도 0개다. 원시 결과 SHA-256은 Claude
`aa6637f0074256a65bb65d04df3e39fd242d7fec70632792512204ea55a469cb`,
Codex `a4263a8a24c5bad6eb4f65b13ff481493d6cbee4cea94ce0153d9d5a48a243ea`이다.
Claude 시작 설정의 첫 자동 실행은 `GUEST_RESULT_error`를 남겼으므로
이 기록을 보존했다. 살아 있는 동일 게스트에서 명시적으로 단발 재실행한
최종 종료 코드 0과 통과 결과만 적재·복원 증거로 사용한다. 시험 후
네 후보 영수증을 다시 검증했고 모두 일치했다. 실제 모델·이미지·Bot
호출, 계정의 크레딧 폴백 차단, 자동 선택 품질, 사용자 설치와 과금 검증은 미완이며
`installation_ready=false`, `host_compatibility_verified=false`,
`runtime_closure_verified=false`를 유지한다. PR #68·#69의 독립 리뷰·
별도 심판 D-code 역시 아직 없어 `main` 머지 근거가 아니다.

## PR #69 명명된 크레딧 버킷 누락 차단 후보 (2026-10-01)

2.12.30 코드 검토에서 최상위 크레딧이 false/false/0이어도 명명된
한도 버킷의 `credits` 필드가 빠지면 계획과 가짜 CLI 발송이 통과하는
결손을 발견했다. RED 회귀를 추가하고 2.12.31에서 각 명명된 버킷의
크레딧 기록을 필수로 하여 차단했다. 이 변경은 실제 계정의 구매 크레딧을
소비하거나 결제 설정을 조작하지 않는다.

새 후보 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-credit-buckets-candidate/`
는 이전 후보를 보존한 채 동일한 고정 원본 5개 커밋에서 빌드했다.

| 산출물 | 전체 digest | 검증 범위 |
|---|---|---|
| `source` | `de3262cd7c922203ff1efb4d91889a1d1890de86327253ecba03aaf6fe89ea8f` | 137스킬·423파일 |
| `candidate-safety` | `93f771c3fbdf392ebc037247ea8b8948438436568770a39603f31c48f5be5c61` | Claude 5플러그인·182스킬 |
| `codex-overlay-safety` | `607aad42a9ab20d0804e31df96486eb1549ffd06d4cfe54f7b96d17b3a8e6898` | Codex 호환 투영 |
| `codex-subset-safety` | `3b4a87e3b885654089e1bc353d6fba1c2991d8ee2ae53732518aee48831fd0cd` | Codex 177스킬·출처 검증 |

네 영수증은 빌드 후와 Sandbox 시험 후 모두 일치했고 오프라인
probe 4/4, `/vibe` 단위 테스트 327건, 자체 점검 180항목, 스킬 품질
141/141, 라우팅 표 동기화가 통과했다. 정확한 후보는
`E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-pr69-buckets-host-rehearsal/`
의 네트워크·클립보드·장치 리디렉션 비활성, 무인증 게스트 두 곳에서
단발 실행으로 검증했다. Claude Code 2.1.285는 5플러그인·182스킬·
디버그 오류 0, Codex CLI 0.155.0은 플러그인 5개 활성. 두 게스트 모두
기존 링크 Claude 5개·Codex 2개를 두 번 복원했고 최종 시험 설치 0개,
모델 생성 0건, 활성 네트워크 0개였다. 원시 결과 SHA-256은 Claude
`0749792db94da54f1496f88e75c6b6ddc69e711900f72d08e2b5eee2453874d9`,
Codex `4bf3bba4269f734cf4879722ed6bedde57bb0a4f9bc08d748a5a2271697997c1`.
두 게스트를 정확한 ID로 종료한 후 `wsb.exe list --raw`는 빈 목록이었다.

이 범위는 무인증 적재·복원이지 실제 사용자 호스트의 자동 선택·effort,
전체 Gstack 런타임, 구독 청구, 이미지·Bot 실행 또는 사용자 설치
증거가 아니다. `installation_ready=false`, `host_compatibility_verified=false`,
`runtime_closure_verified=false`를 유지한다. PR #68·#69의 독립 리뷰와
§35 별도 심판 D-code 없이 `main` 머지하지 않는다.

## One-shot 설치

아래는 기존 경로입니다. 소스 오버레이의 parity 증거를 대신하지 않으며,
네트워크·환경변경을 포함합니다. `--dry`만으로 모든 legacy 부작용의 안전성이
검증됐다고 가정하지 마세요. 새 `/vibe` 운영 이관을 위해 자동 실행하지 않습니다.

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git
cd SimonK-stack
./scripts/install.sh
```

설치되는 것 (2026-05-27 기준):
- `~/.claude/skills/gstack/` — Gstack 풀 트리 (38+ skill + bin/scripts/lib + bun deps, garrytan/gstack upstream)
- `~/.claude/skills/<gstack-skill>/` — 38+ Gstack skill 개별 노출
- `~/.claude/skills/<simon-stack>/` — 100+ simon-stack skill (skills-src/ + .claude/skills/, connect-chrome zombie auto-skip)
- `~/.claude/instincts/` — 4 seed 파일 (mistakes / patterns / korean / quirks)
- `~/.claude/session-start-instincts.sh` — SessionStart hook 스크립트
- `~/.claude/CLAUDE.md` — 글로벌 지침 (instincts auto-load + Boris 원칙 + 100+ skill 카테고리 맵)
- `~/.claude/.simon-stack-installed` — installed SHA marker (session-start.sh selective-update logic 입력)

**기존 파일은 덮어쓰지 않음** — `cp -n` 로직. 재실행 안전.

## 사전 요구사항

- `git`
- `bun` (Gstack 런타임. 없어도 SKILL.md 만 동작하지만 헬퍼 스크립트는 실패)
- `node` ≥ 20 (Claude Code 자체)
- `claude` CLI 설치됨

## 수동 단계 (자동화 불가)

1. **SessionStart hook 등록** — `~/.claude/settings.json` 에 직접 추가:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "~/.claude/session-start-instincts.sh" }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

2. **Claude Code 재시작** — 새 skill 로드를 위해.

3. **트리거 테스트**:
   - "새 앱 만들고 싶어" → `app-dev-orchestrator` 발동
   - "기능 구현해줘" → `dev-orchestrator`
   - "보안 점검" → `security-orchestrator`
   - "권한 시스템 설계" → `authz-designer`
   - "TDD 시작" → `simon-tdd`

## 구성

- **Gstack** (garrytan/gstack): 실행 파이프라인 36개. `/ship`, `/qa`, `/cso`, `/retro`, ...
- **simon-stack** (이 레포): 방법론·보안·학습 24개
  - Orchestrators: `app-dev-orchestrator`, `dev-orchestrator`, `security-orchestrator`
  - Security: `security-checklist`, `authz-designer`, `paid-api-guard`
  - Method: `simon-tdd`, `simon-worktree`, `simon-research`, `simon-instincts`, `agent-delegate`
  - Tools: `code-health-guard`, `simon-design-first`, `nextjs-optimizer`, `stitch-design-flow`, `project-context-md`
  - Meta: `skill-gen-agent`, `context-guardian`
  - General Dev: `commit`, `debug`, `explain`, `refactor`, `review`, `test-gen`

자세한 카테고리 맵: `.claude/skills/INDEX.md`

## 제거

```bash
rm -rf ~/.claude/skills/gstack
# 개별 simon-stack skill 은 수동 제거
# 백업에서 복구:
ls ~/.claude.bak-*  # 설치 시 자동 백업됨
```

## 참고

- [Gstack](https://github.com/garrytan/gstack) — 실행 파이프라인 원본
- [Superpowers](https://github.com/obra/superpowers) — TDD·worktree 철학 원본
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — instincts·research-first 원본
