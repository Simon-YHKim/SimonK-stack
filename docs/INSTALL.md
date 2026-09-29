# Install — simon-stack

이 레포는 Claude Code 를 위한 통합 skill 스택(Gstack + simon-stack + Superpowers 철학)이다.

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
`<base-version>-vibe.<source-digest 앞 12자>`는 후보 표시일 뿐 고유 검증키나 설치
방지 장치가 아닙니다. 원본 JSON과 변환 후 JSON을 모두 검증 기록으로 보존합니다.
이 candidate envelope를 marketplace에 등록하거나 `install.sh` 입력으로 넘기지 마세요.

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
`scripts/candidate_path_audit.py`는 SKILL 본문의 백틱으로 감싼 명시적 **ASCII 파일**
상대경로만 검사하며, 형제 스킬 경로(`../llm-eval/...`)도 같은 플러그인 안에서
해석합니다. 종료 1은 미해결 경로·비이식 명령 또는 외부 Gstack 런타임 참조의
**문맥 검토 필요**이지 파일 누락 확정이나 실행 실패 증명이 아닙니다.
정적 경로만 충족하고 외부 참조가 남으면 `external_runtime_pending`을 반환합니다.
동적 경로·절대 호스트 경로·import·서비스·
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
```

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

## 2026-09-27 frontier 메타데이터와 구독 평가 경계

공식 [OpenAI 모델 안내](https://developers.openai.com/api/docs/models),
[Anthropic 모델 비교](https://platform.claude.com/docs/en/models/overview),
[xAI 모델 안내](https://docs.x.ai/developers/models) 및
[Google Antigravity CLI 안내](https://codelabs.developers.google.com/antigravity-cli-hands-on)를
현재 로컬 목록과 대조했다. GPT-6 Astra/Sol/Luna, Claude Opus 5.5/Fable 5.1/Sonnet 5,
Grok 4.7, Gemini 3.8 Flash는 이미 `model-registry.json`에 있다. 새 API 모델 ID를
발견했다는 이유만으로 구독 포함 실행 레인으로 승격하지 않는다.

v11 후보의 `runtime_collect.py`를 네 표면에 읽기 전용으로 실행해 종료코드 0을
확인했다. 반환된 Codex 후보 7개는 모두 `available=false`,
`billing.verified=false`다. 로컬 `grok models`는 `grok-4.7`을 기본·사용 가능
목록에 표시하지만, ACP billing의 주간 사용량은 89%, on-demand cap/잔액은 0이고
account/billing/model 포함 증거는 미확인이다. `agy models`는 Gemini 3.8 Flash
High/Medium/Low를 표시한다. 이 메타데이터는 생성·과금 방식·호스트 라우팅 성공의
증거가 아니며, Grok/Gemini 모델 실호출은 하지 않았다.

Claude Max `claude.ai`/firstParty 로그인과 API 키·대체 엔드포인트 환경변수 부재를
확인한 뒤, 도구 없는 Opus 5.5 단일 응답 평가를 구독 경로에서 시도했다. CLI는
`modelUsage=claude-opus-5-5`를 표시했으나 `error_max_budget_usd`와 빈 응답을
반환했다. `--max-budget-usd 0.5`에도 CLI `total_cost_usd=3.711888`이 표시되어
이 플래그가 호출 전 결제·사용량 하드캡임을 입증하지 못했다. 이 값은 실제 추가
청구 영수증이 아니며 청구서는 조회하지 않았다. 사용자의 초과 사용·자동충전 OFF
확인을 유지했고 설정 변경이나 추가 모델 재시도는 하지 않았다. 따라서 Opus 5.5의
성공 canary, 모델-쿼터 결합, 구독 전용 라우트 활성화는 계속 **미검증**이다.

## `/vibe` 2.11.15 v14 레거시 CLI 바이트코드 후보 (2026-09-27)

기능 브랜치 `feat/skill-context-budget-260925`의 `e5831d5`에서 평문 Python으로
실행한 레거시 CLI 여섯 종의 첫 로컬 import가 후보 영수증 밖 `.pyc`를 만들지
않도록 수정하고 격리 subprocess 회귀 검사를 추가했다. 마지막 세 종
(`aggregate_ledger.py`, `adversarial_eval.py`, `sync_skill_table.py`)은 수정 전
각각 실패를 재현했다. 모듈로 import하는 다른 호출자는 자체 no-bytecode 정책이
필요하며, 부모 `-B`는 자식 Python에 전파되지 않는다.

기존 후보는 덮어쓰지 않았다. 릴리스 부모
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/`의
`source-v14-legacy-cli-closure` digest는
`93df1319b4960fd9eb6bf7bb226663d68ecd5a02ac6f12841a6f0488112bd20d`
(137 skill/407 file), `candidate-safety-v14-legacy-cli-closure` digest는
`d5f9a10bd8e4521c87adce70482a16303dd228f843db8385dab20069af1847e4`
(5 plugin/182 skill/729 file)이다. 저장소 `/vibe` 테스트 369개와
selftest 180개, 후보 안의 오프라인 테스트 500개가 통과했고, 일반 Python으로
후보의 라우팅 표 검사·평가 CLI 도움말을 실행한 뒤에도 두 영수증을 재검증했다.
저장소 skill validator는 0오류/0경고, eval dry-run은 20케이스 형식 통과다.
Codex 기본 `skill-creator` quick validator는 기존 `version`·`author`
frontmatter를 허용하지 않아 이 저장소의 검증기를 사용했다.

`try-vibe-v14-claude.ps1 -CheckOnly`와 `try-vibe-v14-codex.ps1 -CheckOnly`는
후보만 확인하고 모델을 호출하지 않는다. 별도 Codex 진단 프로필은 5개 플러그인이
enabled이며 후보↔캐시 전체 729파일 SHA-256이 일치하지만 로그인되지 않았다.
실사용 Claude·Codex 홈의 `/vibe`는 2.11.6 그대로다. 모델/Bot/Orca 발송,
결제·인증 설정 변경, 운영 설치와 main 머지는 하지 않았다. 세 readiness 플래그
`runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는
모두 false다. 후보 바이트 검증을 실행 가능성·구독 포함·과금 차단의 증거로
해석하지 않는다. 직접 CLI의 crash/reentry 계약은 허브 §35.1 토론·D-code가
필요하며, 그전에는 레거시 직접 실행을 우회 경로로 사용하지 않는다.

Claude Code 2.1.283의 모델 생성 없는 로컬 명령으로 v14 후보의 다섯
`.claude-plugin/plugin.json`을 각각 `plugin validate --strict --json`으로
검사했다(모두 종료 0, 오류·경고 0). 후보 `plugins/`를 한 번에
`--plugin-dir`로 지정한 `plugin list --json`에는 다섯 플러그인 모두
`@inline`·`scope=session`·`enabled=true`로 나타났다. 각 플러그인의
`plugin details`는 아래 구성요소와 세션당 **Always-on 추정치**를 반환했다.

| 플러그인 | 호스트 열거(스킬+명령) | Always-on 추정 |
| --- | ---: | ---: |
| SimonKAIHub | 8 | ~1,791 tok |
| SimonKCore | 63 | ~13,532 tok |
| SimonKDesign | 23 | ~5,590 tok |
| SimonKMarket | 33 | ~7,554 tok |
| SimonKStack | 60 | ~12,628 tok |
| **합계** | **187 = 182 스킬 + 5 명령** | **~41,095 tok** |

이는 v14의 세션 전용 **발견·매니페스트** 관측이다. CLI의 추정 토큰 수는
실측 컨텍스트 사용량이나 Codex의 설명 예산 경고와 같은 지표가 아니며,
합계가 그대로 청구되거나 모델 응답 품질을 떨어뜨렸다고 주장하지 않는다.
`plugin validate` 결과의 `contents=[]`는 개별 스킬 본문 검증을 뜻하지
않는다. 자동 선택·명시 스킬 호출·훅·비용·영구 설치는 미검증이다. 이 조회
후에도 bundle digest `d5f9a10b…69af1847e4`가 일치했고 readiness3=false다.
상시 노출량을 낮추면서 `/vibe`를 통해 모든 스킬을 호출하는 배포 구조는
§35.1 설계 토론 대상으로 분리한다.

## `/vibe` 2.11.16 v15 레거시 표 참조 후보 (2026-09-27)

기능 브랜치 `feat/skill-context-budget-260925`의 `56fb120`은 과거 Orca
라우팅 표를 `/vibe` 본문에서 직접 연결된
`references/legacy-routing.md`로 옮겼다. 본문은 371→283줄이다. 표의
생성 정본 `routing.py`, 현행 모델 registry, 계정·비용 가드와 실행 경로는
그대로다. 기본 본문 로드 감소는 초기 스킬 **description** 예산이나
자동 선택 정확도 개선의 증거가 아니다.

기존 v14와 설치본을 덮어쓰지 않고 같은 격리 릴리스 부모 아래 새
`source-v15-context-reference`와 `candidate-safety-v15-context-reference`를
만들었다. source digest는
`d856259eea3e563792013afb666866d24e3d114c06a64b020c695c081ab1e8e2`
(137 스킬/409 파일), five-plugin bundle digest는
`84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9`
(5 플러그인/182 스킬)이다. 부모 경로는
`E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/`.
입력 플러그인 5개는 `distribution/plugin-inputs.v1.json`의 pinned commit과
일치했고 빌드 전 clean이었다.

소스 회귀 3건·orchestration 90건·selftest 180건·릴리스 38건·번들
43건이 통과했고, skill validator는 오류 0/경고 0, eval dry-run은
20케이스 형식 통과였다. 첫 병렬 번들 실행의 Windows 임시 폴더 잠금
오류는 단독 케이스 및 전체 43건 단독 재실행에서 재현되지 않았다. 후보
내 표 동기 회귀 3건과 selftest 180건, 정적 링크 142개 미해결 0,
Claude manifest strict 5/5 오류·경고 0을 확인했고 검사 후 bundle
digest가 그대로였다. 부모 `-B`와 별도로 자식 Python에도
`PYTHONDONTWRITEBYTECODE=1`을 적용했다.

Claude Code 2.1.283의 **모델 생성 없는** 로컬 명령에서 v15 Core만
`--plugin-dir`로 로드하면 `simonk-core@inline` 한 개가 세션 enabled이고
호스트 목록은 Core 스킬 63개, Always-on 추정치는 약 13,532토큰이다.
Core에 있는 `/vibe`의 후보 내 오프라인 `catalog`는 고정된 5개 플러그인
스킬 182개를 찾았다. 이는 Core-only 기본 노출 + 전체 로컬 카탈로그
탐색의 가능성을 보여주지만, 다른 네 플러그인의 호스트 고유 Skill 호출,
훅·명령 실행이나 동등한 사용성은 검증하지 않는다. v14의 5-plugin 동시
노출 추정 41,095토큰과 두 추정치의 차이는 실제 컨텍스트 절감량이나
구독 사용량·요금 차이로 해석하지 않는다. 배포 구조 선택은 허브 §35.1
설계 토론 후 결정한다.

세 readiness 플래그 `runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 계속 false다. 실사용 Claude·Codex 설치본은
2.11.6이고, 운영 설치·main 머지·모델/Bot/Orca 실호출·결제/인증 설정
변경은 하지 않았다. source의 `routing.py` 상단 한 줄은 아직 표가
`SKILL.md`에 생성된다고 적어 실제 참조 파일 위치와 다른 문서 드리프트로
남아 있다. 다음 소규모 수정에서 바로잡는다.

### v15 구독 경로의 단일 Claude 선택 테스트와 제한된 미리보기

Claude Max 로그인(`claude.ai`/firstParty), API 키·대체 엔드포인트 환경변수
부재, 사용자가 확인한 초과 사용·자동충전 비활성화를 전제로 Sonnet 5 `low`의
짧은 읽기 전용 선택 테스트 **1건**을 실행했다. `--tools Skill`, plan mode,
v15 Core만 `--plugin-dir`로 지정했을 때 기록된 `Skill` 입력은
`simonk-core:vibe`였고, 최종 답은 `/vibe`를 선택했다. 실제 콘솔 접근,
Bot·Orca 디스패치나 파일 변경은 없었다. 후보 digest와 실사용 홈의
2.11.6 버전은 검사 후 불변이었다. 이는 **한 프롬프트의 명시적 호출**이며,
자연어 자동 선택 정확도나 다른 181개 스킬의 동작 검증이 아니다.

이 호출에서 Claude CLI는 3턴과 `total_cost_usd=3.856994`를 보고했다.
이는 구독 사용의 **API 단가 환산치**이지 추가 청구 영수증이 아니다.
고유 모델 응답 2건의 로컬 기록에는 cache-creation 입력 276,232 및
687,242토큰이 있었다. `--tools Skill`만 허용해도 모델 요청에
claude.ai MCP 도구 정의가 각각 239개와 669개 포함됐다. 이 기록만으로
어떤 개별 플러그인·스킬이 그 증가를 유발했는지 단정할 수 없지만,
반복 실호출 전 불필요한 커넥터 노출을 줄여야 한다는 강한 신호다.
`--setting-sources ''`와 `--tools Skill`만으로 연결 도구 목록이 사라진다고
가정하지 않는다. 공식 [Claude Code 환경변수 안내](https://code.claude.com/docs/ko/env-vars)는
`ENABLE_CLAUDEAI_MCP_SERVERS=false`로 claude.ai MCP를 끌 수 있다고 한다.

그래서 `scripts/preview-vibe-candidate.ps1`을 추가했다. 기본 호출은 후보
영수증·Core 플러그인만 검사하고 **모델을 호출하지 않는다**:

```powershell
pwsh -NoProfile -NonInteractive -File scripts/preview-vibe-candidate.ps1 `
  -CandidateRoot 'E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/candidate-safety-v15-context-reference' `
  -ExpectedDigest 84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9
```

도구 제한 라우팅 세션은 위 명령에 `-Run -SubscriptionOnlyConfirmed`를
**명시적으로** 더할 때만 시작된다. 다섯 플러그인을 함께 시험하려면
`-AllPlugins`도 추가한다. `-AllPlugins`만 주면 5개 플러그인의 파일 존재와
후보 digest를 확인하고 모델을 호출하지 않는다. `-Run`은 대화형 세션으로
열리며 사용자가 입력한 프롬프트가 구독 사용량을 소비한다.
`-Model`은 기본 `claude-sonnet-5` 또는 명시적 `claude-sonnet-5-5`만 허용한다.
실행 시 새 빈 임시 작업 폴더에서 시작해 호출 저장소의 프로젝트 지침·권한을
시험에 섞지 않으며, 예기치 않은 파일이 생긴 임시 폴더는 지우지 않는다.
정확한 Max 구독 로그인과 API/대체 제공자 환경변수 부재를 재검사하며,
그 자식 프로세스에만
`ENABLE_CLAUDEAI_MCP_SERVERS=false`를 설정하고 `--strict-mcp-config`,
기본 Core-inline 한 개 또는 명시된 5-plugin, 허용 목록의 Sonnet 모델 `low`,
`dontAsk` 권한 모드, `Skill` 도구만 사용한다. `Skill`만 사전 허용하고
`mcp__*`는 명시 차단하고 권한 프롬프트도 사용하지 않는다.
[Claude Code 권한 문서](https://code.claude.com/docs/en/permissions)의
`dontAsk`는 미승인 도구를 프롬프트 대신 거부하며,
[CLI 참조](https://code.claude.com/docs/en/cli-reference)의 `--tools`는
모델에 보이는 내장 도구를 제한한다. 이는 플러그인 훅·호스트 시작 동작까지
격리하는 OS 샌드박스가 아니다.
이 절 작성 당시에는 환경변수 차단과 호스트 컨텍스트 절감 효과를 아직
실측하지 않았다. 아래의 2026-09-28 관측이 이를 부분적으로 보충한다.
실행기는 사용자에게 설정 확인을
요구하지만 초과 사용 비활성화를 기계적으로 증명하지 못한다. 일반 작업
실행이나 설치가 아닌 라우팅 미리보기이며 GUI/봇/Orca 조작은 불가하다.
새 테스트는 RED 3건을 재현한 뒤 GREEN 3건 및 실제 v15 후보
`CheckOnly` 1건 및 가짜 API 키 차단 1건을 통과했다. 가짜 키가 있을 때 `-Run`은 모델 시작 전
`NON_SUBSCRIPTION_CREDENTIAL_PRESENT`로 차단됐다.
2026-09-28 추가 회귀 테스트는 새 `-AllPlugins` 호출이 없어서 RED였고,
가짜 Claude 호스트를 통한 다섯 `--plugin-dir`·`dontAsk`·`Skill` 사전 허용·
MCP 차단·프로세스 로컬 플래그를 검증한 뒤 전체 6/6 GREEN이었다.
이 테스트는 실제 모델 호출이나 훅 동작 증거가 아니다.

### v15 커넥터 억제와 비-Core Skill 호스트 관측 (2026-09-28)

같은 v15 후보를 변경하지 않고 Claude Max 구독 경로에서 Sonnet 5 `low`의
추가 읽기 전용 테스트 2건을 수행했다. 사용자 확인대로 초과 사용·자동충전은
꺼진 상태이며 API 키·대체 제공자 환경변수는 없었다. 두 테스트 모두
`ENABLE_CLAUDEAI_MCP_SERVERS=false`를 해당 자식 프로세스에서만 적용했고,
`--setting-sources '' --strict-mcp-config --tools Skill`을 사용했다.
첫 테스트는 Core-inline만 로드해 한 단어 응답을 요청했다. 모델 요청에
도구 정의는 `Skill` 1개, claude.ai MCP 정의 0개였고 한 턴에서 끝났다.
CLI `total_cost_usd=0.093304`는 API 단가 환산치이며 청구 영수증이 아니다.
고유 응답의 cache-creation 입력은 23,315토큰이었다. 반면 이전의 플래그
미적용 테스트에는 claude.ai MCP 정의가 각 요청에 239개·669개 실렸다.
도구 정의 제거는 관측했지만, 두 테스트의 프롬프트·턴 수가 다르므로
cache-creation 차이 전체를 플래그의 절감량으로 계산하지 않는다.
공식 [Claude Code 환경변수 안내](https://code.claude.com/docs/ko/env-vars)도
이 플래그의 커넥터 비활성화 용도를 명시한다.

두 번째 테스트는 다섯 플러그인을 함께 로드해
`simonk-market:aha-moment-optimizer`의 실제 `Skill` 호출과 정상 도구 결과를
관측했다. 이때도 MCP 도구 정의는 0개였다. 그 뒤
`Skill` 도구에 존재하지 않는 `ExitPlanMode` 이름을 전달해 도구 오류가 1건
발생했다. CLI 최종 종료 코드는 0이지만 이를 완전한 호스트 동작 통과로
간주하지 않는다. 명시 호출의 한 예가 통과한 것이며 전체 182개 스킬의
자동 선택·훅·실제 작업 결과는 아직 검증되지 않았다. 두 호출 모두
추가 결제 설정, Bot/Orca 발주, 후보 파일 변경 없이 끝났고 번들 digest는
`84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9`로
재검증됐다.

현 사용자 Codex CLI 0.155.0의 `codex plugin list --json`에는 설치 플러그인
20개 중 SimonK 네이티브 항목이 없다. 이는 loose skill 경로의 노출과
별개의 사실이다. 앞 절의 격리 Codex 프로필 5-plugin 등록 증거를 사용자
홈의 네이티브 설치로 확대 해석하지 않는다. OpenAI의
[로컬 플러그인 문서](https://developers.openai.com/plugins/build/plugins)는
저장소·개인 marketplace와 로컬 캐시 설치 방식을 구분한다. 현재 후보에는
각 플러그인의 Claude-compatible marketplace 파일이 있지만, 후보 envelope
전체의 운영 marketplace 등록·사용자 Codex 설치는 수행하지 않았다.
Codex `skill-creator`의 보조 `quick_validate.py`는 후보 `/vibe`에 있는 기존
`version`·`author` frontmatter 키를 허용하지 않아 종료 1을 냈다. 182개
SKILL.md 모두 `version` 키를 가진다. 저장소의 Claude용 validator는
`/vibe` 오류 0·경고 0이며, 앞 절의 격리 Codex 플러그인 등록도 통과했다.
따라서 이 차이는 **Codex 작성용 linter와 기존 배포 형식의 차이**로 기록하고,
실제 Codex 로더가 182개를 거부한다는 증거로 확대하지 않는다. Codex 전용
정규화 패키지가 필요한지는 설치·행동 실측 후 별도 설계 판정으로 다룬다.
`plugin_bundle.py`는 후보 영수증의 세 readiness 값을 의도적으로 항상
`false`로 생성·검증하므로, 단순 호스트 호출 성공이나 영수증 재검증만으로
승격할 수 없다. 별도 release 검증·승격 계약과 §35 설계 판정이 남아 있다.

### v15 다섯 플러그인 `dontAsk` 호스트 재시험 (2026-09-28)

위의 `ExitPlanMode` 오류를 재현한 `plan` 모드는 `Skill`만 제공하는
세션의 목적과 맞지 않았다. 실행기에는 명시 `-AllPlugins` 옵션과
`dontAsk`+`Skill` 사전 허용+MCP 도구 차단을 추가했다. 이 권한 모드 변경은
사용자·프로젝트 설정에 기록하지 않고 해당 Claude 자식 세션에만 적용된다.
가짜 Claude 호스트 회귀 테스트는 수정 전 `-AllPlugins` 미지원 RED,
수정 후 전체 6/6 GREEN이었다. 이 테스트는 실제 모델 동작을 증명하지 않는다.

별도의 단발 실제 호출은 동일한 다섯 `--plugin-dir`, Sonnet 5 `low`,
`dontAsk`, `--allowedTools Skill --tools Skill --disallowedTools 'mcp__*'`,
`ENABLE_CLAUDEAI_MCP_SERVERS=false`, `--setting-sources ''`,
`--strict-mcp-config`, `--permission-prompts none`, 최대 3 agentic turns로
실행했다. Max/claude.ai/firstParty 로그인·대체 API 환경변수 0개를 호출 직전에
확인했다. 스트림 관측은 `Skill=simonk-market:aha-moment-optimizer` 1건,
도구 결과 1건, 최종 `is_error=false`, 정확한 응답, CLI 종료 0이었다.
이 한 예에서 후속 `ExitPlanMode` 오류가 사라졌지만 전체 스킬 행동·훅·명령·
자동 선택 정확도 또는 구독 청구액을 증명하지 않는다. 후보 digest는 다시
일치했고 사용자 설치본·결제 설정·Bot/Orca는 변경하지 않았다.

### v15 Claude 안전 훅 실측과 Codex 이식 경계 (2026-09-28)

격리된 빈 임시 작업 디렉터리에서 Claude Max/Sonnet 5 `low` 구독 경로로
Core `simonk-core:careful`과 별도 Stack `simonk-stack:guard`를 각각 명시
호출했다. 두 세션 모두 `Skill`과 `Bash(printf *)`만 허용하고
`dontAsk`·권한 프롬프트 없음·MCP 차단을 적용했다. 각 세션은
`printf 'SAFE_PROBE'`류 명령과, **문자열만 출력하는**
`printf '%s' 'git reset --hard'` 명령을 요청했다. 실제 reset 명령은
요청하거나 실행하지 않았다.

두 세션의 로컬 호스트 기록에는 각각 `PreToolUse:Bash` 훅 실행 성공이
2건씩 있었다. 안전한 `printf`는 실행됐고, reset 문자열을 포함한
`printf`에는 각각 `permissionDecision=ask`가 반환돼 승인 표면이 없는
세션에서 도구 실행이 거부됐다. 이는 **Claude Code 2.1.283에서 두
스킬의 훅 로딩·차단을 관측한 대표 사례**다. 위험 문자열을 단순 출력해도
보수적으로 막는 위양성도 함께 관측했다. 이 두 임시 작업 디렉터리는 비어
있음을 확인해 제거했다.

별도의 Claude Max/Sonnet 5 `low` 세션에서는 Stack `freeze`를 호출하고
임시 프로젝트 안에 세션별 경계를 미리 설정했다. `Write`로 경계 밖의 새
파일을 만들려는 요청은 `PreToolUse:Write hook error: [freeze] Blocked`로
거부됐고, 경계 안의 새 파일은 생성됐다. 실제 사용자 프로젝트에는 쓰지
않았다. 같은 조건의 `investigate` 시험에서는 모델이 축약된 스킬 호출을
거부해 `Skill`·`Write`가 모두 0회였다. 따라서 `investigate` 훅의 호스트
동작은 **미검증**이다. `freeze`의 상태 해제, 다른 도구·플랫폼과 전체
스킬도 아직 실측 대상이다. 안전 훅 단위 테스트 28/28은 통과했고 후보
digest는 재검증됐다. 이 추가 시험의 임시 파일 3개와 디렉터리는 삭제
명령이 실행 정책에 막혀 보존돼 있다. 사용자 설치본에는 영향이 없다.

후보 182개 SKILL.md 중 `hooks:` frontmatter를 가진 것은 위의 `careful`,
`guard`, `freeze`, `investigate` 네 개이며, 5개 플러그인 어디에도 Codex
플러그인용 `hooks/hooks.json`은 없다. OpenAI의
[플러그인 패키징 문서](https://developers.openai.com/plugins/build/plugins)에
따르면 Codex 플러그인 훅은 `hooks/hooks.json` 또는 명시된 hook 설정으로
발견되며, 설치·활성화만으로 신뢰되지 않아 사용자의 현재 정의 검토가
필요하다. 이것은 **Codex가 SKILL frontmatter 훅을 실행하지 않는다는
실측 증명은 아니지만**, 현재 후보로 동등한 안전 훅 정책을 주장할 근거도
없다는 뜻이다. 현 사용자 Codex 네이티브 설치 목록 20개에는 SimonK가
0개였다. Codex 쪽 실제 훅 계약·신뢰 절차·격리 호스트 동작을 확인하기
전에는 Claude의 통과를 Codex 설치 준비 완료로 승격하지 않는다.

추가로 [Codex 공식 훅 계약](https://learn.chatgpt.com/docs/hooks)은
`PreToolUse`의 `permissionDecision: "ask"`를 **미지원**으로 명시한다.
Codex는 이 값을 훅 실패로 보고하고 원래 도구 호출을 계속할 수 있으므로,
Claude `careful`/`guard`의 승인 요청을 Codex에 그대로 연결하면 안전 정책이
동등해지지 않는다. Codex의 `apply_patch`는 `Edit`/`Write` matcher에 걸릴 수
있지만 실제 입력은 `tool_input.command`이며, 현재 freeze 런타임의
`tool_input.file_path` 전제와 다르다. 이는 공식 계약과 후보 코드의 **정적
불일치**로, 아직 Codex 호스트에서 위험 명령이나 패치 차단을 실측한 결과가
아니다. Codex 승격에는 네이티브 훅 등록·사용자 신뢰 외에도 지원되는
`deny`/실패 처리, 명령 및 패치 경계 안·밖의 허용/차단, 롤백을 각각
확인해야 한다. 훅은 일부 특수 도구에 적용되지 않을 수 있어 완전한 보안
경계로 간주하지 않는다.

적용 **범위**도 별도 설계가 필요하다. 공식 문서는 활성 플러그인의
`hooks/hooks.json`을 플러그인 훅으로 로드하고 matcher에 맞는 도구 호출에
적용한다고 설명한다. 반면 현재 네 안전 스킬은 Claude `SKILL.md`의
skill-scoped frontmatter 훅이다. 현 freeze 런타임은 해당 프로젝트·세션의
상태 파일이 없거나 무효하면 `deny`로 닫는다(오프라인 회귀 재통과).
이를 Codex의 전역 플러그인 훅으로 **그대로** 등록하면 일반 세션의
`apply_patch`도 거부할 수 있다는 것은 계약·소스에서 나온 추론이며,
Codex 호스트 실측은 아니다. 스킬 활성화 신호·세션 상태·미활성 시 동작을
정하지 않은 채 훅 파일만 추가해서는 안전 동등성이나 사용성을 얻지 못한다.

### Codex 안전 훅의 선택형 프로필 경로 (2026-09-28, 제안·미적용)

기존 허브 D-29·D-30의 안전 스킬 미지원 표시와 단계적 승격 결정을
유지한다. 공식 [Codex 설정 계층](https://learn.chatgpt.com/docs/config-file/config-basic)은
`codex --profile <name>`이 사용자 기본 설정 위에 별도 프로필 파일을
올리는 방식을 지원하고, [고급 설정](https://learn.chatgpt.com/docs/config-file/config-advanced)은
활성 설정 계층의 inline 훅을 설명한다. 따라서 일반 Codex 세션의
플러그인 훅을 켜지 않은 채, 명시적으로 선택한 `simonk-guarded` 같은
CLI 프로필에서 Codex 전용 훅을 시험하는 경로가 있다. **프로필 훅의
실제 로딩·신뢰·도구 차단은 아직 실측하지 않았으며 프로필 파일도
설치하지 않았다.** Desktop/IDE 동등성도 이 CLI 근거에서 추론하지 않는다.

2026-09-28 `ai-debate`의 세 입장(기본 플러그인 훅/현행 보류/선택형
프로필)과 별도 심판은 선택형 프로필을 *다음 개발 후보*, 현행 보류를
*배포 상태*로 권고했다. 소수의견은 프로필·상태 영수증 자체가 복잡성을
늘리므로 오프라인 어댑터만 유지하자는 것이다. 이는 Claude 소유
DECISIONS D-code에 아직 승격되지 않은 **제안**이며, D-29·D-30을
뒤집지 않는다. Codex의 `ask` 미지원, `apply_patch`의
`tool_input.command`, 훅 오류 시 호출 지속 가능성, 도구 적용 예외 때문에
Claude 안전 런타임을 그대로 연결하지 않는다. 향후 프로필 후보에는
현재 세션에서 신뢰된 훅 실행 증거, 미활성 세션의 정상 작업, 위험 Bash
차단, 경계 안팎 패치, 상태 손상·재개·철회와 사용자 프로필 롤백을
분리해 검사해야 한다. 그 전에는 `/vibe`가 네 안전 스킬의 Codex 정책
집행을 주장하지 않고 세 readiness 플래그도 `false`다.

선행 오프라인 입력 어댑터 `scripts/codex_hook_input.py`는 현재
`PreToolUse` JSON의 `Bash`·`apply_patch` `tool_input.command`를
1 MiB 이하로 읽고, 패치의 Add/Update/Delete/Move 대상 경로를
목록화한다. 중복 키·중복/빈 경로·알 수 없는 지시문·불완전한 패치는
`HookInputError`로 거부한다. `python -B -m unittest discover -s
scripts/tests -p test_codex_hook_input.py -v`의 5개 회귀 테스트가 통과했다.
이 어댑터는 **도구 명령을 실행하지 않고**, 경로 정규화·안전 정책 결정·
훅 등록·프로필 설치·실제 호스트 동작을 구현하지 않는다. 구독 모델이나
Bot을 호출하지 않은 계약 파서 시험만으로 안전 집행을 주장하지 않는다.

후속 오프라인 후보 `scripts/codex_guarded_policy.py`는 해당 파서를 사용해
Codex `PreToolUse`가 지원하는 `deny` JSON만 반환한다. 명시적 `--bash`와
`--careful-script`가 주어지면 기존 careful leaf를 격리 환경에서 실행하고
Claude 전용 `ask`를 **차단**으로 바꾼다. 선택적 `--boundary`가 있으면
`apply_patch`의 모든 선언 경로(이동 목적지 포함)의 실제 부모·링크를
확인하고 경계 밖 또는 판단 불가 입력을 차단한다. 경계가 없으면
패치는 제한하지 않으며, 검사가 실패하면 차단한다. 입력 명령 자체는
실행하지 않는다. `python -B -m unittest discover -s scripts/tests -p
test_codex_guarded_policy.py -v`의 11개 사례와 전체 Codex 관련 26개
사례가 통과했다. 이 후보는 **고정 경계의 로컬 시험용**이며 세션별
활성화·신뢰 영수증·프로필 등록·실제 호스트 집행 및 Shell을 통한
파일 쓰기 차단은 제공하지 않는다. D-29·D-30의 미지원/보류 판정은 유지한다.

2026-09-28 **격리 호스트 실측**: Windows Sandbox의 Codex CLI 0.155.0에
일회용 `simonk-guarded.config.toml`을 만들고 `SessionStart` 마커 훅만
등록했다. 게스트의 활성 네트워크 어댑터 0개, `auth.json` 부재, 주요 API
키 환경변수 부재를 확인했다. 실제 `codex exec` 세션에서 기본 프로필과
신뢰되지 않은 선택형 프로필은 모두 마커가 없었고, 선택형 프로필에
**그 게스트 호출 한 번에만** `--dangerously-bypass-hook-trust`를 준 경우
`SessionStart` 이벤트 마커가 남았다. `codex debug prompt-input`에서는
같은 우회 플래그를 줘도 훅이 실행되지 않아, 디버그 출력만으로는 훅
집행을 검증할 수 없다. 세 `exec`는 네트워크 차단 때문에 응답 생성 없이
12초 후 종료시켰다. 이는 프로필 선택과 신뢰 게이트의 부분 증거일 뿐,
실제 사용자 프로필의 훅 신뢰, `PreToolUse` 차단, Desktop/IDE 동작,
모델 응답 또는 요금 검증이 아니다. 실사용에 우회 플래그를 권장하지
않으며 프로필·플러그인·설치본은 설치하지 않았다. 원시 결과는
`E:/Coding Infra/Releases/SimonK-stack/20260928-codex-profile-host-probe/output/result.json`에
있다. 세 readiness 플래그는 여전히 `false`다.

2026-09-28 **격리 정책 직접 실행**: 별도 Windows Sandbox에서
`scripts/codex_guarded_policy.py`와 입력 파서·careful leaf 및 Python/Git Bash/Node
실행 파일의 SHA-256 7개를 확인한 후, 합성 `PreToolUse` 입력 5개를 정책
프로세스에 전달했다. 경계 안 패치·안전 Bash는 허용하고 경계 밖 패치·
파괴적 Bash·안전 런타임이 빠진 Bash는 각각 차단해 5/5 기대 결과가
일치했다. 게스트의 활성 네트워크 어댑터는 0개였고 계정 `auth.json`과
주요 API 키 환경변수는 없었다. 이 검사는 정책 **직접 호출**에 한정된다.
Codex의 `PreToolUse` 훅 등록·집행, 실제 모델 행동, 사용자 프로필,
Shell을 통한 파일 쓰기 차단 또는 결제 상태를 입증하지 않는다.
인증·모델 호출 없이 끝냈고 시험 게스트를 종료했다. 재현 스크립트와
원시 결과는 `E:/Coding Infra/Releases/SimonK-stack/20260928-codex-policy-sandbox/`
에 있으며 readiness 플래그는 계속 `false`다.

### Codex 호환 오버레이 v2 (2026-09-28, 설치 전 후보)

`scripts/codex_overlay.py`는 고정된 v15 5-플러그인 후보를 **읽기 전용**으로
검증하고 별도 경로에 복사해 Codex 호환 `.codex-plugin/plugin.json` 다섯 개를
추가한다. Stack의 수동 전용 `zoom-out`은 오버레이 복사본에서만 기존
`disable-model-invocation: true`를 제거하고
`skills/zoom-out/agents/openai.yaml`의
`policy.allow_implicit_invocation: false`로 투영한다. [OpenAI 공식 플러그인
검증 규격](https://developers.openai.com/plugins/deploy/submission-errors)은 이
정책 필드를 정의한다. 원본 후보·사용자 설치본은 바꾸지 않는다.

```powershell
python -B scripts/codex_overlay.py build `
  --candidate 'E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/candidate-safety-v15-context-reference' `
  --candidate-digest 84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9 `
  --output 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v2-candidate'
python -B scripts/codex_overlay.py verify `
  --package 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v2-candidate' `
  --overlay-digest 545cc8967404a710f09cfdbbbcd9e75f1856dce6a5a10533f3fb9631360c8228
```

오버레이 영수증은 원본 후보 digest와 일곱 투영 파일의 바이트를 묶는다.
원본 스킬 바이트도 저장해 후보 영수증과 대조하며, 추가·변조 파일은 거부한다.
2026-09-28 로컬 `plugin-creator` 검증기는 5/5 플러그인을 통과시켰다.
새 빈 `CODEX_HOME` 검사 홈에 후보의 로컬 marketplace 다섯 개를 등록하고
다섯 플러그인을 설치한 결과 `codex plugin list --json`에서 모두
`installed=true`, `enabled=true`였다. 검사 홈은 `codex login status`에서
`Not logged in`이며 모델 호출은 없었다. 검사 캐시의 737개 파일은 후보와
경로·SHA-256이 모두 일치했고, 검사 뒤 오버레이 digest도 재검증됐다.
번들·오버레이 회귀 테스트 49/49도 PASS였다
(`python -B -m unittest scripts.tests.test_plugin_bundle scripts.tests.test_codex_overlay`).
이는 **패키지 등록·복사 검사**일 뿐, Codex 모델의 실제 스킬 선택·실행,
훅 신뢰·동작, 사용자 홈 설치·롤백 검증이 아니다. 특히 Claude 스킬
frontmatter 안전 훅 네 개를 Codex 훅으로 옮기지 않았다. 영수증의
`installation_ready`와
`host_compatibility_verified`는 계속 false이며, 운영 설치 전환의 근거로
사용하지 않는다. 모델 호출이나 별도 과금은 이 빌드·검증에 필요 없다.

같은 날 별도 미로그인 프로필
`E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-rollback-probe`에서
로컬 marketplace 5개 등록 → 플러그인 5개 설치 → `codex plugin remove`
5회 → `codex plugin marketplace remove` 5회의 **격리 롤백 리허설**을 했다.
설치 직후 다섯 개 모두 `installed=true`, `enabled=true`였고, 제거 후
SimonK 설치 목록 0·마켓플레이스 설정 0·캐시 파일 0을 확인했다. 빈 캐시
상위 디렉터리 5개는 남는다. 기존 v2 검사 프로필의 설치 5개와 후보
digest는 변경되지 않았다. 이는 빈 테스트 프로필의 신규 설치를 철회한
증거일 뿐, 기존 사용자 홈의 2.11.6 파일·설정·활성 세션을 보존하며
되돌리는 운영 롤백 검증은 아니다. 따라서 위 readiness 플래그는 그대로다.

별도의 빈 `CLAUDE_CONFIG_DIR`
`E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-claude-rollback-probe`에서도
같은 v15 원본 후보의 로컬 marketplace 5개 등록 → Claude 플러그인 5개
설치·활성화 → 설치 캐시와 후보의 731개 파일 경로·SHA-256 일치 확인 →
플러그인 5개 uninstall → marketplace 5개 remove를 모델 호출 없이 실행했다.
마지막 `claude plugin list --json`은 빈 목록이고 marketplace 설정도 0이다.
다만 Claude CLI의 uninstall은 복사된 캐시를 삭제하지 않고 각 버전 폴더에
`.orphaned_at`을 추가했다. 테스트 프로필에 **캐시 파일 736개(원본 복사본
731개 + 표시 5개)**가 남았으며, 이 파일들은 수동 삭제하지 않고 보존했다.
따라서 이 리허설은 **등록·활성 상태 철회**만 입증하고 디스크 캐시 정리나
기존 사용자 프로필 2.11.6의 무손실 운영 롤백을 입증하지 않는다. 실제 사용자
설정·설치본, 결제 설정, 원본 후보 및 위 readiness 플래그는 변경하지 않았다.

### D-29 Codex 일반 스킬 전용 하위 후보 (2026-09-28, 설치 전)

허브의 별도 심판 판정 `D-29`는 현재 v15 Codex 후보의 `careful`, `guard`,
`freeze`, `investigate` 정책 집행을 **미지원**으로 표시한다. 일반 스킬만
제공하려면 네 안전 스킬 디렉터리를 제외하고 그 한계를 고지한 별도 후보가
필요하다. 이 결정은 훅 신뢰·차단 실측을 대신하거나 사용자 설치를 허용하지
않는다. 허브 `DECISIONS.md`의 D-29는 현재 로컬 공유 작업트리에만 있고,
허브 원격 동기화·정식 릴리스 판정은 별개다.

`scripts/codex_safe_subset.py`는 검증된 v2 오버레이를 읽어 위 네 스킬과
`freeze`에 종속된 Claude 전용 `unfreeze`, Core/Stack의 `.simonk-runtime/`
안전 런타임을 제외한 불변 복사본과 `subset.json` 영수증을 새 경로에 만든다.
초기 v1 하위 후보는 `unfreeze`와 런타임이 남아 있어 이 검토에서 탈락했고,
원본 보존을 위해 그대로 두었다. 아래 v2가 현재 검증 대상이다.
영수증은 포함·제외 파일의 경로·크기·SHA-256, 원본 오버레이 digest,
`D-29`, 두 readiness=false 플래그를 고정한다. 검증 시 원본 오버레이를
같이 제공하면 원본→하위 후보의 바이트 출처도 다시 대조한다. 원본 v15와
v2 오버레이는 변경하지 않는다.

```powershell
python -B scripts/codex_safe_subset.py build `
  --source-overlay 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v2-candidate' `
  --overlay-digest 545cc8967404a710f09cfdbbbcd9e75f1856dce6a5a10533f3fb9631360c8228 `
  --output 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-general-subset-v2'
python -B scripts/codex_safe_subset.py verify `
  --package 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-general-subset-v2' `
  --subset-digest d1b93f09a9bd84d4a8e72bb51a065782b62572a9c0c5e3a5738b7e9e4968cc80 `
  --source-overlay 'E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v2-candidate' `
  --overlay-digest 545cc8967404a710f09cfdbbbcd9e75f1856dce6a5a10533f3fb9631360c8228
```

로컬 v2 후보는 5플러그인·177개 `SKILL.md`이며 위 다섯 스킬과 두 안전
런타임 디렉터리가 없다. 공식 `plugin-creator` 검증기는 5/5,
번들·v2 오버레이·하위 후보 회귀는 54/54 통과했다. `/vibe`를 다섯 스킬
루트와 함께 명시적 `--root`로 호출한 인벤토리는 177개·문제 0건이었다.
하위 후보에는 원본의
182개짜리 `bundle.json`이 출처 자료로 남으므로 기본 번들 탐색의
성공을 주장하지 않는다. 분리 설치된 Codex 캐시에서는 현재 호스트가
관측한 다섯 루트를 명시적으로 넘기는 split-home 절차가 필요하다.
v2도 새 미로그인 격리 `CODEX_HOME`
`E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-general-subset-hostprobe-v2`
에서 5개를 설치·활성화했다. 캐시 714파일이 후보와 경로·SHA-256 일치했고
177개 스킬 중 `/vibe`는 1개, 제외된 안전 스킬은 0개였다. 이어 정확한
5개 플러그인·마켓플레이스를 제거해 설치 목록·마켓플레이스·캐시 파일
모두 0으로 확인했다. 이는
**설치 복사·목록·철회** 증거이지 모델의 177개 스킬 선택, 일반 스킬의
안전성, Codex 훅 집행 또는 사용자 홈 무손실 롤백 증거가 아니다. 다른
스킬 문서나 README가 제외된 안전 스킬을 언급할 수도 있으므로 실행 전에는 실제
호스트의 스킬 목록과 누락 의존성을 대조한다. 이 하위 후보도
`installation_ready=false`, `host_compatibility_verified=false`다.

### D-30 v15 호스트별 배포 승격 게이트 (2026-09-28, 로컬 판정)

별도 심판 판정 `D-30`은 현재 사용자 설치본 2.11.6을 유지하고, 원본 v15
5플러그인·182스킬을 **격리 사이드바이사이드 환경**에서 전체 패키지 의존성·
복원 리허설로 먼저 검증한 뒤 Claude 제한 파일럿을 검토한다. 실제 사용자
프로필의 백업·롤백 계획은 그 파일럿 **착수 전**에 별도로 확인한다.
Codex 전체 승격에는 네이티브 훅 패키징·신뢰 절차·허용/차단 실측이
추가로 필요하다. D-29 일반 스킬 하위 후보의 복사 검증은 이 전체
승격 게이트를 대신하지 않는다.

Claude 안전 훅은 `careful`·`guard`·`freeze`의 **제한된 호스트 사례 3/4**만
관측됐다. `freeze`는 Write 경계 안·밖 한 사례이고 Edit·해제·세션 종료는
미검증이며, `investigate`는 모델이 호출을 거부해 훅 관측 0건이다. 나머지
178개 일반 스킬의 실제 행동도 검증되지 않았다. 세 readiness 플래그는
모두 `false`이고 사용자 설치 전환·`main` 머지·결제 설정 변경은 없다.
허브 `DECISIONS.md`의 D-29·D-30은 현재 로컬 공유 작업트리에 기록됐지만
허브 원격은 기존부터 분기돼 있어 아직 동기화하지 않았다.

v15 후보의 로컬 `/vibe` 회귀 검사는 원본을 실행하지 않고 영수증 검증 후
임시 폴더에 복사하여 실행한다. 원본·복사본을 실행 전에, 원본을 실행 후에
`bundle.json` digest와 전체 파일 바이트로 재검증한다. 자식 프로세스는
임시 사용자 프로필을 쓰며 API 키 환경변수를 상속하지 않는다.

```powershell
python -B scripts/candidate_runtime_probe.py --package '<candidate>' --expected-digest '<bundle_digest>'
```

2026-09-28 v15(`84e8759f…4386bf9`)에서 `/vibe` selftest, 런타임 단위
테스트, 준비 절차 테스트, 스킬 표 동기화 검사의 4단계가 통과했다. 앞선
원본 직접 테스트로 생긴 `.pyc` 6개는 별도 복구 가능 격리 폴더로 옮기고
원본 영수증 검증을 복구했다. 이 검사는 **OS 샌드박스가 아니며** 전체
182스킬의 실행 의존성·호스트 동작·설치 복원 증거가 아니다. 따라서 세
readiness 플래그는 계속 `false`이고 사용자 설치 전환 게이트도 그대로다.

추가 정적 점검에서 v15의 7개 스킬에 `skills-src/` 경로 표기가 13곳
남아 있음을 확인했다(`code-health-guard`, `dev-orchestrator`,
`llm-wiki-builder`, `model-router`, `simon-research`, `simon-tdd`,
`simonk`). 후보 루트에는 `skills-src/`가 없으므로 배포 환경에서 이
표기를 그대로 실행하는 절차는 자체완결성이 없다. 또한 31개 스킬의
본문에 외부 Gstack 실행 파일 탐색 코드가 포함되지만 해당 `bin/`은 이
후보에 묶이지 않는다. 이것은 **정적 의존성 결손/외부 의존성 목록**이지
31개 스킬 모두의 실행 실패 실측은 아니다. 표기 교정·외부 런타임 계약과
격리 재검증 전에는 전체 package closure를 완료로 판정하지 않는다.

## `/vibe` 2.11.16 v16 경로 폐쇄 후보 (2026-09-28)

소스의 `code-health-guard`·`simon-tdd`·`dev-orchestrator`·`llm-wiki-builder`·
`simon-research`·`model-router`·`simonk`에 있던 프로젝트 상대
`skills-src/` 실행 안내를 설치 스킬 루트 또는 개발 전용 소스 루트로
구분했다. 원본 SimonKStack의 `data-retention-planner`와
`release-health-guard`도 활성 `SKILL.md`의 부모 경로에서 helper를
찾도록 수정했다(원본 브랜치 `fix/skill-validation-260927`, 로컬 커밋
`beb2a547`). `distribution/plugin-inputs.v1.json`은 해당 커밋을 고정한다.

원본 SimonKCore 작업트리에는 추적되지 않는 기존 모델 캐시와 의미 인덱스가
있어 번들러의 정확한 입력 목록 검사가 차단됐다. 원본 캐시는 삭제·이동하지
않고, 다섯 원본의 고정 커밋을 별도 로컬 디렉터리
`input-clones-v16-path-closure`에 복제하여 빌드했다. 이전 v15 후보와
사용자 설치본도 변경하지 않았다.

| 항목 | 격리 검증 결과 |
|---|---|
| 소스 패키지 | `source-v16-path-closure`, digest `e20dcc1e98e971411143fec50bd50dc743d1358455ff35582d68b5d9a085cb68`, 137스킬·409파일 |
| 5-플러그인 후보 | `candidate-safety-v16-path-closure`, digest `5cbef02fbee7ee0777b694f44e3d6cdbe61f16ec28144c91a4ccbdef87f03d0a`, 182스킬·731파일 |
| 원본 Stack 검증 | 저장소 검사 통과, 수정 2스킬 validator 오류·경고 0, eval 6케이스 dry-run 통과, 관련 스크립트 구문 검사 통과 |
| 패키징 회귀 | 소스 릴리스 38건, 플러그인 번들 44건, 경로 감사 14건 통과 |
| 정적 경로 감사 | 182스킬, 명시 참조 142건 모두 존재, 미해결 0·비이식 실행 명령 0 |
| 오프라인 `/vibe` 회귀 | 영수증 검증 후 격리 복사에서 selftest·runtime unit·prepare unit·table sync 4단계 통과 |

경로 감사기의 후속 확장은 같은 검증된 v16 후보에서
`external_runtime_hints`로 Gstack `bin/` 참조 스킬 31개를 별도 보고한다
(검사 단위 테스트 17/17). 이 목록은 **외부 의존성 힌트**이지 해당 스킬의
실행 실패 31건이나 런타임 가용성 증명이 아니다. 정적 경로 142건 통과와
구분하며 감사 명령은 `external_runtime_pending`/종료 1,
`runtime_closure_verified=false`를 그대로 유지한다.

공식 Gstack 원본을 사용자 홈 설치본과 분리된 로컬 읽기 전용 조사 복제본
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-upstream-audit`에서
확인했다(HEAD `01593aa67c94780528e8f5121e47362502410ced`, `VERSION`
`1.91.2.0`, MIT). 현재 복사된 31개 스킬은 구형 인라인 preamble인 반면
원본은 호스트별 스킬 생성과 `gstack-skill-start/end` 런타임을 사용한다.
따라서 최신 `bin/`만 덧붙여 호환성을 주장할 수 없다. 원본 setup·의존성
설치·사용자 홈 Gstack 접근은 하지 않았다.

후속으로 고정 원본의 생성 함수만 별도 출력 디렉터리
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-render-probe`에
실행했다. Claude용 54스킬/106산출물, Codex용 55스킬/112산출물이
생성됐고 두 호출 모두 종료 0이었다. Codex 생성기는
`plan-ceo-review`(약 40K토큰)와 `ship`(약 53K토큰)의 40K토큰 상한 초과를
경고했다. 생성물은 별도 Gstack 런타임을 찾아 실행하므로 문서 생성만으로
후보 자체완결성이나 컨텍스트 예산 적합성을 증명하지 않는다.

Windows Sandbox의 별도 로컬 게스트에서는 네트워크·클립보드·vGPU를
비활성화하고 보호 클라이언트를 켰다. 고정 원본·Git Bash·생성 문서는
읽기 전용으로, 결과 폴더만 전용 쓰기 경로로 매핑했다. 게스트의 활성
네트워크 어댑터는 0개였다. 원본 `gstack-skill-start`/`end`를 게스트
전용 상태에서 `update_check=false`, `telemetry=off`,
`artifacts_sync_mode=off`로 실행한 결과 각각 종료 0, 시작 프로토콜 1,
종료 outcome=success가 기록됐다. 소유자가 다른 읽기 전용 Git 복제본은
첫 조회가 `dubious ownership`으로 차단됐으며, 전역 설정을 바꾸지 않고
해당 조회 한 번에만 `safe.directory`를 지정해 원본 HEAD 일치를 확인했다.

같은 격리 방식의 별도 게스트 프로젝트에서 생성된 `canary`의 Claude·Codex
전처리 Bash 블록을 각각 **생성 문서 그대로** 추출해 실행했다. 두 문서의
SHA-256은 호스트 생성본과 일치했고 모두 종료 0·시작 프로토콜 1을
반환했다. 각 모델 오버레이는 `claude`·`gpt`, 업데이트·telemetry·동기화는
꺼진 상태였다. 근거 파일은 `20260928-gstack-runtime-sandbox/output/`와
`20260928-gstack-hostlink-sandbox/output/`에 있다. 시험 게스트는 닫았고
게스트 임시 상태만 폐기됐으며, 호스트 결과 파일은 보존했다.

선언된 스킬 이름으로 두 생성 목록을 기존 후보와 대조하면, 외부 참조
31개 중 Claude 생성본에 대응하는 이름은 30개, Codex 생성본은 29개다.
`checkpoint`는 양쪽 원본 생성 목록에 없고, `codex`는 Codex 생성 목록에
없다(그 호스트에는 별도 `claude-code`가 생성된다). 외부 참조 힌트가 없는
기존 `careful`·`freeze`·`guard`·`spec`·`unfreeze`도 upstream 생성 이름과
겹친다. 새 생성본에만 있는 이름은 Claude 19개, Codex 21개다. 따라서
31개를 54/55개로 일괄 치환하거나 동명 안전 스킬을 덮어쓰는 설계는
별도의 소유권·별칭·훅 의미 검토 없이 진행할 수 없다.

`scripts/gstack_migration_audit.py`는 검증된 후보와 별도 생성 폴더를
읽기 전용으로 대조한다. 파일명 대신 생성 `SKILL.md` frontmatter의 선언 이름을
매칭하고, 없어진 로컬 정책 제목·500줄 초과 본문을 확인한다. 경로 감사는
선언된 스킬 폴더의 보조 Markdown까지 포함하여 생성 폴더 절대 링크·
사용자 홈 Gstack 링크(`~`, `$HOME`, `${HOME}`)를 검토 항목으로
보고한다. 비밀이 들어갈 수 있는 명령문이나 본문은 출력하지 않는다.

```powershell
python -B scripts/gstack_migration_audit.py `
  --package 'E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-helper-closure-candidate/candidate-safety-v16-path-closure' `
  --expected-digest 5cbef02fbee7ee0777b694f44e3d6cdbe61f16ec28144c91a4ccbdef87f03d0a `
  --generated-root 'E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-render-probe' `
  --expected-claude-digest f8b896bb5cd71b9cc4978feaecbdf2bc5a19cbef9a222ca5173eab881e83a385 `
  --expected-codex-digest 852be775940075d52e5953ddc76a52ab4498266fa676bb6cc6fb99be7b8e87af
```

2026-09-28 실측: legacy 31개 중 Claude 생성 이름 30개·Codex 29개 대응,
누락은 Claude `checkpoint`, Codex `checkpoint`·`codex`다. 각 호스트의
생성 문서 24개가 500줄을 넘었다. 기존 문서에만 있는 선택 정책 제목은
완료 보고 59쌍, Skill routing 57쌍, `investigate` 세션 범위 2쌍이었다.
두 생성 digest를 지정한 재검사에서 `generated_bytes_verified=true`이고
감사 결과는 `migration_review_required`/종료 1이며 검증기 단위 테스트
9건이 통과했다. digest는 선택된 생성 `SKILL.md`의 상대 경로와 바이트를 고정하며
런타임·보조 파일이나 원본 Git 커밋과의 생성 관계는 검증하지 않는다.
전체 Markdown 바이트는 별도의 `generated_markdown_digests`로 고정하며,
`--expected-claude-markdown-digest`와 `--expected-codex-markdown-digest`를
함께 지정할 때만 `generated_markdown_bytes_verified=true`다. 이 플래그는
제공한 digest와의 바이트 일치일 뿐 원본 출처나 실행 가능성 증명이 아니다.

생성 관계의 별도 재현 확인(2026-09-28): 작업트리가 깨끗한 격리 Gstack
`01593aa67c94780528e8f5121e47362502410ced`에서
`scripts/gen-skill-docs.ts`의 `runGeneration`을 Claude·Codex 각각 실행해
두 기대 digest가 모두 재현됐다. 이때 `contentLinkRoot`를 최초 생성본과 같은
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-render-probe`처럼
슬래시(`/`) 문자열로 전달했다. Windows CLI의 `--link-root`는 이를
백슬래시(`\`) 경로로 정규화해 Claude 생성 문서 20개의 섹션 링크 바이트가
달라진다(Codex digest는 동일). 그러므로 이 재현은 **특정 커밋·옵션·경로**의
문서 바이트 증거일 뿐, 이식 가능한 생성물이나 런타임 폐쇄성의 증거는 아니다.
제목 부재는 **동일 의미의 부재 증명**이 아니고,
생성 폴더의 upstream 출처·런타임 동작·호스트 호환성도 이 감사기가
증명하지 않는다. 세 readiness 플래그는 계속 false다.
생성 폴더를 그대로 검사하면 Claude 문서 20개의 섹션 링크 47곳이 해당
생성 폴더의 절대 경로를 가리킨다(Codex 0곳). 설치 경로가 달라지면 이
링크들을 다시 생성·검증해야 한다. 감사기의 `generated_root_links`는
이 폴더를 가리키는 리터럴만 세며 모든 외부 경로를 포괄하지 않는다.
또한 Claude 생성 문서 49개에 `~/.claude/skills/gstack/` 리터럴 884곳이
있다(Codex 0곳). 생성기의 `contentLinkRoot=null`도 상대 링크를
만드는 대신 같은 사용자 홈 경로를 남긴다. 감사기의
`generated_user_home_gstack_links`는 이 정확한 접두어만 세며 실제 사용자
홈을 탐색하지 않는다. 따라서 문서 자체만 플러그인으로 복사해도 Gstack
런타임·섹션 의존성이 폐쇄된다고 간주할 수 없다.

호스트별 이식 경계: [Claude 플러그인 공식 문서](https://code.claude.com/docs/en/plugins/components#reference-plugin-paths-and-store-data)는
스킬 본문의 `${CLAUDE_PLUGIN_ROOT}`를 버전별 설치 경로로 치환한다고 명시한다.
반면 고정 Gstack 원본의 `hosts/claude.ts`는 `usesEnvVars: false`이며
사용자 홈 리터럴 경로를 생성한다. 따라서 Claude 플러그인에 번들할 경우
호스트별 경로 재작성과 실제 설치 경로·섹션·런타임 검증이 필요하다.
[Codex 플러그인 공식 문서](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks)는
`${PLUGIN_ROOT}`를 플러그인 **훅 프로세스**에 제공한다고 설명하지만,
스킬 본문 치환까지 보증하지 않는다. 고정 Gstack Codex 생성본은
`$HOME/.codex/skills/gstack` 또는 프로젝트 `.agents/skills/gstack`에서
`$GSTACK_ROOT`를 정하므로, 해당 경로가 설치 플러그인 런타임과 실제로
결속되는지 별도 호스트 시험 전에는 가정하지 않는다.

Windows 런타임 자산 조사(2026-09-28): 위 Claude 생성 `SKILL.md`의 정적
`~/.claude/skills/gstack/` 참조를 고정 원본 커밋의 파일과 대조하면,
빌드 산출물인 `bin/gstack-cso-launcher`/`.exe`, `design/dist/design`,
`bin/gstack-global-discover`가 원본 트리에 없다. 이는 정적 문자열의
부분 감사이며 동적 의존성이나 전체 런타임 폐쇄성을 증명하지 않는다.
별도 로컬 빌드 복제본 `20260928-gstack-build-probe`에서 네트워크·모델 호출
없이 Bun으로 `gstack-global-discover.exe`, `design.exe`, `gstack-cso-core.exe`
3개를 컴파일했다. 합계 347,122,688바이트(약 331 MiB)이며 Git Bash에서는
앞의 두 `.exe`를 확장자 없는 경로의 `test -x`로 찾았다. 그러나 CSO의
보안 경계인 네이티브 `gstack-cso-launcher.exe`는 빌드하지 못했다.
고정 원본의 Windows 빌드는 Visual Studio 2022 MSVC/Windows SDK를
요구하며 이 PC의 스크립트 지정 경로에는 `vswhere.exe`가 없다. 따라서 이 세 컴파일 성공을
CSO 또는 Gstack 전체의 실행 가능 판정으로 승격하지 않는다. 바이너리
크기도 전체 번들 크기가 아닌 세 산출물만의 측정치다. 런타임 포장 방식과
설치 경로 정책은 별도 아키텍처 결정 후 선택한다.

같은 네트워크 차단 게스트의 별도 실행에서는 첫 `gstack-skill-start` 뒤
`gstack-skill-end`를 의도적으로 생략하고, 동일한 게스트 상태에서 두 번째
시작·종료를 수행했다. 시작 2회는 모두 종료 0·프로토콜 1을 반환했고
두 세션 ID는 달랐다. 두 번째 종료는 종료 0·success를 기록했다. 근거는
`20260928-gstack-runtime-sandbox/output/reentry-*`에 보존했다. 이것은
**종료 누락 후 재진입** 시험이지 시작 도중 프로세스 크래시, 상태 손상,
외부 송신 복구 또는 사용자 설치본 롤백의 증거가 아니다.

v16 후보를 별도의 새 빈 `CLAUDE_CONFIG_DIR`
`E:/Coding Infra/Releases/SimonK-stack/20260928-v16-claude-rollback-probe`에
등록·설치했다가 철회하는 리허설도 모델 호출 없이 수행했다. 호스트의
`claude plugin validate --strict --json`은 5개 매니페스트 모두 종료 0·
오류/경고 0이지만 `contents=[]`여서 본문 검증으로 해석하지 않는다.
테스트 프로필에서 설치 5개가 모두 활성화됐고 캐시 731개 파일의 경로와
SHA-256이 v16 후보 영수증과 일치했다. 5개 uninstall 및 5개 marketplace
remove 후 설치 목록과 등록 marketplace는 각각 0개다. 다만 CLI가 캐시를
삭제하지 않아 원본 복사본 731개와 `.orphaned_at` 표시 5개, 총 736개가
테스트 프로필에 남았으며 삭제하지 않고 보존했다. 원본 후보의 digest는
재검증했다. 이는 **빈 프로필 등록·복사·활성·철회** 증거일 뿐 기존 사용자
프로필의 무손실 운영 롤백이나 182개 스킬 실행 증거가 아니다.

같은 v16 후보를 `scripts/codex_overlay.py`로 별도
`E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v16-candidate`에
Codex 호환 투영했다(overlay digest
`2b7aec29b2a3c746a4ff21fb5ceb61482c6ffd0203d7058f8f572926ba31047c`).
번들·오버레이 회귀 49/49, 플러그인 validator 5/5, overlay 재검증이 통과했다.
새 빈 `CODEX_HOME`
`E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-codex-overlay-v16-rollback-probe`에서
로컬 marketplace 5개 등록 → 플러그인 5개 설치·활성 → 캐시 파일 737개
경로·SHA-256 일치 확인 → 5개 플러그인·marketplace 철회를 모델 호출 없이
리허설했다. 철회 후 테스트 설치 0·marketplace 0·캐시 파일 0이며,
사용자 Codex의 SimonK 설치는 전후 0개, overlay digest도 불변이었다.
제거된 것은 이 빈 테스트 프로필에 새로 복사한 캐시 737개뿐이고 후보
원본은 보존했다. 이는 Codex의 **격리 등록·복사·롤백** 증거이지
실제 스킬 선택·안전 훅·전체 동작 또는 기존 사용자 프로필의 롤백 증거가 아니다.

이것은 **대표 스킬의 시작/종료 및 호스트 경로 연결 시험**일 뿐이다.
`canary` 본문 작업, 안전 훅, 기존 31개 복사본과 새 런타임의 호환성,
전체 182개 동작, 프로세스 중단/복원, 모델 선택·추가 과금, 사용자 설치본 롤백은 확인하지
않았다. 격리 설정과 어댑터 0개 관측은 비용 영수증이나 모든 네트워크
시도의 부재 증명이 아니다.

정적 경로 감사는 리터럴 참조와 알려진 프로젝트 상대 명령만 다룬다.
동적 import, 외부 Gstack 실행 파일, 호스트 권한·안전 훅, 모델 선택 행동,
Bot/Orca 실연결, 모든 스킬의 동작은 검증하지 않는다. 후보 manifest의
`runtime_closure_verified`·`host_compatibility_verified`·
`installation_ready`는 계속 모두 `false`다. 모델 실호출·추가 과금·
사용자 설치 전환·`main` 머지는 수행하지 않았다.

구독 전용 비용 가드 후보(2026-09-28): 기능 브랜치 `789920b`의 `/vibe`
2.12.0은 로컬 명령의 `setup`·스모크 테스트에 숨은 API 호출도 비용 계약에
포함하도록 명시한다. 고정 Gstack `01593aa`의 디자인 CLI는 `setup`에서
이미지 생성 스모크 테스트를 실행하고, `generate`·`check`가 OpenAI API 키로
API를 호출하므로 추가 과금 $0·구독 포함 전용에서는 세 명령을 실행하지
않는다. 다른 디자인 작업은 개별 감사하며 전체 스킬을 일괄 금지하지 않는다.
이를 반영한 새 격리 source v17 digest는
`7e6c77cef6bc90676f222ce8a7a50cdb45f5c337a3777f6de66055fddb4d0467`
(137스킬·409파일), 5-plugin 후보 digest는
`4533352ac5ee2621f961d6d8c28cb4b8d61fef8deec1e1d81de95fd657d2e4fb`
(182스킬·731파일), Codex overlay digest는
`9840de039b5f8ccfcc32930b01f0e156dceced1964a514cffba45cc316fca0b5`다.
세 영수증 재검증, 번들·오버레이 회귀 49/49, `/vibe` 라우팅 90/90,
selftest 180/180, 스킬 validator 오류·경고 0 및 새 평가 케이스 형식
검사가 통과했다. 평가 케이스의 **모델 행동 시험은 실행하지 않았다**.
정적 경로 감사는 여전히 외부 Gstack 의존 31개로
`external_runtime_pending`/종료 1이며 세 readiness 플래그는 모두 false다.
이 후보는 설치·호스트 동작·구독 청구 안전성의 실측 증거가 아니다.

v17 빈 프로필 등록·복사·철회 리허설(2026-09-28): Claude Code 2.1.283의
`plugin validate --strict --json`은 다섯 manifest 모두 종료 0·오류/경고 0,
그러나 `contents=[]`라 스킬 본문 검증은 아니다. 새 전용
`CLAUDE_CONFIG_DIR`에서 로컬 marketplace 5개와 플러그인 5개를 설치·활성화,
캐시 731파일의 상대 경로·크기·SHA-256이 후보 영수증과 전부 일치했다.
철회 뒤 설치·marketplace는 0개이며 CLI가 보존한 캐시 736파일
(원본 복사 731 + `.orphaned_at` 5)은 삭제하지 않았다. 별도의 새
`CODEX_HOME`에서 Codex CLI 0.155.0의 로컬 marketplace·설치 5개를
확인했고, 오버레이 737파일의 경로·크기·SHA-256이 캐시와 전부 일치했다.
정확한 시험 프로필·소스 경로를 재확인한 뒤 다섯 설치와 marketplace를
철회해 설치 0·marketplace 0·캐시 0이 됐다. 제거된 737개는 이 시험
프로필에서 새로 만든 캐시 복사본이며 후보 원본은 보존했다. 세 후보
영수증은 철회 뒤 재검증됐고 사용자 Codex의 SimonK 네이티브 설치는 0개다.
이는 **빈 프로필 복사·철회** 증거이지 기존 사용자 프로필의 운영 롤백,
스킬 선택·안전 훅·전체 동작 또는 비용 안전성의 증거가 아니다.
별도 저장소 validator로 후보 `SKILL.md` 182개를 전수 검사하면 오류 0,
권고 경고 34개다. 긴 참고 문서의 `## Contents` 부재(W013) 32개와
400줄 소프트 제한 초과(W007) 2개이며, 이 경고만으로 행동 실패나
Gstack 생성 문서의 자동 재작성 필요성을 단정하지 않는다.

## `/vibe` 2.12.1 v18 로컬 비용 검증 후보 (2026-09-28)

기능 브랜치 `feat/skill-context-budget-260925`의 `7543901`은 로컬 도구
견적에 `transitive_effects_audited=true`와 `billing_mode=nonmetered|metered`를
요구한다. 0달러라는 숫자만 적은 견적이나 내부 호출을 감사하지 않은
wrapper는 무료 경로로 인정하지 않는다. 이는 호스트가 수행한 전이 효과
감사의 선언을 검증할 뿐, 임의의 프로그램 내부를 자동으로 분석해 비용이
없음을 증명하지 않는다. TDD의 여섯 실패 케이스 확인 뒤 라우팅 92/92,
run-state 40/40, selftest 및 eval JSON dry-run이 통과했다.

기존 v17·사용자 홈을 덮어쓰지 않고 새 격리 부모
`E:/Coding Infra/Releases/SimonK-stack/20260928-v18-local-cost-guard/`에
다음 세 산출물을 생성했다.

| 산출물 | 검증 digest | 범위 |
|---|---|---|
| `source-v18` | `9f1abd11fa3b648fe12ed1dc78183881e236d957bde007002cda61ece69567f8` | 137스킬·409파일 |
| `candidate-safety-v18` | `2f49c092d816802863b41ad6c194f066d5ae1bfbca30bd522d68c2fac8295cb5` | 5플러그인·182스킬·731파일 |
| `codex-overlay-v18` | `2a30ea29979f5f5d3a09c12cd7561fae92921c1b6c5781d4d9ee4776097ecfcd` | 5플러그인·737 payload 파일 |

첫 후보 빌드는 원본 `SimonKCore`의 Git 무시 모델 캐시 11개 때문에
패키저의 정확한 추적 파일 대조에서 차단됐다. 원본 캐시는 보존하고
`clean-plugin-inputs/`에 다섯 고정 commit을 새로 로컬 복제했다. 복제본
HEAD가 입력 핀과 각각 일치하고 무시·미추적 파일이 없는 것을 확인한 뒤
동일한 source package로 빌드했다. 실패한 첫 시도는 후보를 게시하지 않았다.

세 영수증 재검증 PASS, 격리 후보 런타임 시험 4단계 PASS, 번들 44/44와
Codex 오버레이 5/5 회귀 PASS. Claude strict manifest와 Codex
`plugin-creator` 검증은 각각 5/5 통과했다. Claude 검증의 `contents=[]`는
스킬 본문 동작 증거가 아니다. 182개 SKILL 전수 validator는 오류 0,
권고 경고 34(W013 32·W007 2)이며 v17과 같다. 정적 경로 감사는
참조 142개 중 미해결 0·비이식 명령 0이지만 외부 Gstack bin 참조
31개로 `external_runtime_pending`/종료 1이다.

Gstack 경고 31개는 서로 다른 실행 파일 31개가 아니라, `SKILL.md` 31개에
`gstack/bin/` 문자열이 있다는 뜻이다. 이 문서들의 직접 참조 646곳은
`gstack-config`(305), `gstack-slug`(87), `gstack-telemetry-log`(66),
`gstack-update-check`(62), `gstack-timeline-log`(33),
`gstack-learnings-search`(30), `gstack-repo-mode`(30),
`gstack-team-init`(30), `gstack-learnings-log`(3)의 9개 Bash helper로
모인다. `candidate_path_audit.py`의 `external_runtime_counts`도 v18의
문서 31·문자열 646·고유 대상 9를 반환하지만 종료 1/보류 상태는 유지한다.
이 결과에는 대상 이름이나 명령 본문이 출력되지 않는다. 고정 업스트림
`01593aa`는 9개를 모두 추적하고 실행 비트
`100755`를 기록하며 Git Bash 구문 검사도 9/9 통과했다. 이는 **직접 참조
분류**일 뿐 전이 실행 의존성의 폐쇄나 설치 적합성 검증이 아니다.
`gstack-update-check`의 네트워크 접근, telemetry의 로컬 기록·동기화,
config/team helper의 상태 변경 가능성을 별도 감사해야 한다. 기존
preamble과 새 호스트별 생성 문서의 차이, Windows CSO launcher 부재도
남아 있으므로 9개 스크립트를 후보에 단순 복사하거나 이 검사만으로
준비 상태를 올리지 않는다.
고정 업스트림의 정적 전이 예로 telemetry-log→telemetry-sync,
timeline-log/learnings-log→brain-enqueue, update-check→egress-lib 및
조건부 `supabase/config.sh`, 여러 JSON 처리 경로→Bun이 있다. 이 목록은
전이 의존성 전수 조사나 네트워크·상태 격리의 증명이 아니다.

v18 후보 digest `2f49c092d816802863b41ad6c194f066d5ae1bfbca30bd522d68c2fac8295cb5`를
고정 생성본의 두 digest와 다시 대조한 결과, 생성 바이트 핀은 일치했지만
`gstack_migration_audit.py`는 `migration_review_required`/종료 1이었다.
기존 31스킬 중 생성 이름 대응은 Claude 30·Codex 29이며, Claude 생성본에
테스트 폴더 절대 링크 47곳과 사용자 홈 Gstack 링크 884곳이 남아 있다.
읽기 전용 감사기의 첫 경로 구성요소 분류에서 Claude 홈 링크 884곳은
`bin` 636, `scripts` 78, `docs` 78, 기타 자산·스킬 43,
동적·루트 표현 49로 정확히 합산됐다(Codex 0). 이 집계는 명령 본문·
경로값을 출력하지 않으며 각 링크의 실행성·이식 가능성을 증명하지 않는다.
2026-09-28 보정: 위 47·884건과 구성요소 분류는 당시 `SKILL.md`만
집계한 값이다. 감사 범위를 같은 생성 폴더의 보조 Markdown까지 넓혀
Claude 102개(스킬 54·보조 48), Codex 55개를 검사했다. Claude에서는
생성 폴더 절대 링크 51건/24파일, `~/.claude/skills/gstack/` 1,106건/79파일,
`$HOME`·`${HOME}` 표현 합계 180건/69파일이 확인됐다(Codex는 각 0건).
홈 리터럴 1,106건의 첫 구성요소는 `bin` 818, `scripts` 78, `docs` 78,
기타 자산·스킬 83, 동적·루트 49이며, 서로 다른 경로 표현의 발생 횟수를
독립 파일 수로 합산하면 안 된다. 전체 Markdown digest는 Claude
`6ef0da0c230116654f723496d4439b7c294bea1d5b7765a8f6f0e9538bfa2383`,
Codex `da8072df0d6a265bba065c9f5783898c8d964f5bae72455e2c8f94d7bbcad894`다.
작업트리가 깨끗한 고정 원본 `01593aa67c94780528e8f5121e47362502410ced`에서
`runGeneration`을 별도 `20260928-gstack-regenerated` 폴더에 다시 실행하고
원래 `contentLinkRoot` 문자열을 지정한 뒤 두 전체 digest와 파일 수가
일치함을 확인했다. 이는 해당 커밋·옵션의 정적 생성 재현이며 런타임·
호스트 호환성 또는 이식 완료 증명이 아니다. 재감사도
`migration_review_required`/종료 1이다.
고정 원본의 실제 파일과 대조한 추가 범위 제한 감사: Claude 생성 Markdown
102개에서 `~`·`$HOME`·`${HOME}` 뒤의 `bin/`, `scripts/`, `docs/` 바로 다음
정적 이름만 추출하면 1,089회, 고유 이름 60개(`bin` 56개)다. 이 중 원본
트리에 없는 이름은 `gstack-cso-launcher`, Windows용
`gstack-cso-launcher.exe`, `gstack-global-discover` 세 개다. 앞의 둘은
CSO 네이티브 빌드 산출물이고, 마지막은 `bin/gstack-global-discover.ts`의
Bun 컴파일 산출물이다. 이는 첫 경로 구성요소 감사일 뿐 중첩 경로·
동적 표현·실행 조건·전이 의존성 전체의 폐쇄성 증명이 아니다.

`gstack-global-discover.ts`를 원본을 수정하지 않는 별도 로컬 폴더에서
`bun build --compile`한 결과 Windows 실행 파일 생성·`--help` 종료 0을
확인했다. 파일 크기는 115,431,424바이트(약 110 MiB), SHA-256은
`498c00e826f483cb3c5ae2f90452640bb303b216300c3816e2032a27ac6194fa`다.
현재 overlay 영수증의 파일당 8 MiB·전체 64 MiB 한도를 이 **파일 하나가**
초과한다. 고정 원본의 일반 `scripts/build.sh`는 이외에도 browse 2개,
design·make-pdf 컴파일 파일과 CSO 빌드를 요구하며, 원본 트리에는 이
배포 산출물이 없다. Windows CSO 빌드 검사도 위에서 기록한 MSVC/SDK
부재로 통과하지 못했다. 따라서 현 포맷에 컴파일 산출물을 단순 복사하는
방식은 불가능하며, 패키징 선택에는 포맷 한도·외부 런타임·플랫폼별
빌드 및 완전성 영수증을 함께 결정해야 한다. 이 증거만으로 게이트를
올리거나 기존 사용자 설치본을 바꾸지 않는다.

단, 위 `gstack-global-discover`의 **컴파일 바이너리**가 `retro global`
경로의 필수 전제라는 뜻은 아니다. 고정 원본에서 생성된 `retro/SKILL.md`는
현재 작업 폴더의 `bin/gstack-global-discover.ts`가 보이면
`bun run bin/gstack-global-discover.ts`로 대체하는 fallback을 갖는다.
2026-09-28 무인증·네트워크 차단 Windows Sandbox에서 SHA-256으로 확인한
동일 소스를 게스트 내부 디스크에 복사해 이 정확한 명령을 실행했다.
`--since 1d --format json` 종료 0, 세션·저장소 각 0개였으며
`node_modules` 없이 동작했다. 읽기 전용 공유 폴더에서 Bun이 소스를 직접
열려던 첫 시험은 `EPERM`이었고, 게스트 내부 복사 뒤의 재시험만 통과했다.
원시 결과는 `20260928-gstack-source-probe/output-fallback/result.json`에
보존했다. 이는 이 단일 스크립트와 빈 게스트 프로필의 기능 증거다.
fallback은 **현재 작업 폴더**에 `bin/`이 있어야 하므로, 다른 프로젝트에서
플러그인으로 호출될 때의 경로 계약은 해결하지 않는다. Bun 설치 자체도
영수증 외부이며 browse·design·CSO 빌드 요구, 보조 문서 경로,
네트워크·상태 부작용은 그대로 남는다. 따라서 전체 런타임 준비나
readiness 플래그를 올리지 않는다.

Claude 보조 문서 경로 계약 추가 확인(2026-09-28): 생성 스킬 본문
54개와 보조 Markdown 48개를 분리하면, 보조 파일 35개에도 기존 경로가
남아 있다(`~/.claude/skills/gstack/` 222건, shell HOME 48건,
렌더 폴더 절대 링크 4건). [Claude 플러그인 변수 공식 문서](https://code.claude.com/docs/en/plugins-reference#where-each-variable-resolves)는
`${CLAUDE_PLUGIN_ROOT}` 치환을 **스킬·명령·에이전트 Markdown 본문**에
명시하지만, Bash 도구 환경에 자동 전달하지 않는다. 보조 문서를 Read로
열 때도 같은 치환을 한다는 계약은 여기서 확인되지 않으므로, 본문만
바꾸거나 보조 파일에 리터럴 변수를 넣는 방식의 완전성을 가정하지 않는다.

[Claude SessionStart 훅 공식 문서](https://code.claude.com/docs/en/hooks#persist-environment-variables)는
`CLAUDE_ENV_FILE`에 export를 기록하면 후속 Bash 명령에서 사용할 수
있다고 설명한다. 이 경로의 제한 실측으로 네트워크·클립보드·vGPU를
차단한 Windows Sandbox의 새 무인증 프로필에서 Claude Code 2.1.283과
최소 플러그인을 시험했다. 훅 없는 RED에서 `claude plugin validate`와
`claude --init-only --plugin-dir`는 종료 0, 기대한 훅 마커는 없었다.
`SessionStart` 훅을 추가한 GREEN에서 같은 두 명령이 종료 0, 훅이
`CLAUDE_PLUGIN_ROOT=C:/probe-input/plugin`을 관측하고 세션 env 파일에
`export SIMONK_GSTACK_ROOT='C:/probe-input/plugin'`을 실제로 기록했다.
격리 출력은 `20260928-gstack-env-hook-probe/output-green`에 보존했고
게스트는 종료됐다. 이는 플러그인 훅→Bash env 파일 전달만 증명한다.
보조 Markdown 경로 재작성, CwdChanged 이후의 export 갱신(공식 문서는
이때 이전 값을 지운다고 명시), PowerShell 도구·Codex 동작, Gstack
런타임과 전체 설치는 여전히 미검증이다. 사용자 설치·main·결제 설정과
세 readiness 플래그는 변경하지 않았다.

원본 생성기는 Claude 링크 루트를 절대 경로로 정규화하고 Claude 문서에는
사용자 홈을, Codex 문서에는 별도 `$GSTACK_ROOT` 탐색을 사용한다. 현재
5플러그인 후보 영수증에 고정 Gstack 런타임은 포함되지 않는다. 호스트별
경로 어댑터·런타임 영수증·동명 스킬 소유권을 결정하기 전에는 단순 복사로
설치 후보를 만들 수 없다. Windows 네이티브 CSO 공식 빌드의 `-CheckOnly`도
이 PC에서 Visual Studio 2022 MSVC/SDK가 없어 종료 1이었다. 도구 설치는
시도하지 않았다.

별도 Windows Sandbox helper 시험
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-helper-sandbox/`에서는
네트워크·클립보드·vGPU를 끄고 고정 원본 `01593aa`·Git·Bun 1.3.11을
읽기 전용으로 매핑했다. 첫 게스트의 직접 helper 9종 호출은 8/9 종료 0:
`gstack-learnings-log`만 Bun의 읽기 전용 매핑
`lib/jsonl-store.ts` import에서 `EPERM`으로 실패했다. 두 번째 게스트는
원본 `bin`·`lib`·`VERSION`을 게스트 내부로 복사하고 해당 TS 파일의
SHA-256 동일성을 확인했다. 읽기 전용 경로의 직접 Bun import는 다시
종료 1/`EPERM`이었지만 로컬 복사 import와 helper 9/9는 종료 0이었다.
전후 활성 네트워크 어댑터는 0개였고 `update_check=false`,
`telemetry=off`, `artifacts_sync_mode=off`에서 telemetry usage JSONL·
brain queue는 없었다. 새 게스트 repo의 `CLAUDE.md`와 게스트 Gstack
상태 파일만 생성됐고, 두 게스트는 결과 수집 뒤 종료했다. 상세 증거는
`gstack-helper-sandbox-report.html` 및 같은 폴더의 `output/`에 있다.
이는 Sandbox 읽기 전용 매핑·Bun 조합의 문제를 분리한 제한 시험이지,
실제 플러그인 캐시나 182스킬·Windows CSO 런타임의 동작 증거가 아니다.

v18 Claude 빈 프로필 리허설(2026-09-28): 새 전용
`CLAUDE_CONFIG_DIR=E:/Coding Infra/Releases/SimonK-stack/20260928-v18-claude-rollback-probe`
에서 로컬 marketplace 5개를 등록하고 Claude Code 2.1.283으로 플러그인
5개를 설치·활성화했다. 설치 캐시 731파일의 상대 경로·크기·SHA-256이
`candidate-safety-v18` 영수증과 모두 일치했고 후보 digest 재검증도
통과했다. 이어서 시험 프로필의 플러그인 5개와 marketplace 5개를 철회한
뒤 목록은 각각 0개였다. CLI가 보존한 캐시 736파일(복사본 731개와
`.orphaned_at` 5개)은 삭제하지 않았다. 상세 결과는 같은 Releases 부모의
`20260928-v18-claude-rollback-report.html`에 있다. 이것은 **빈 프로필의
로컬 설치·복사·활성·철회** 증거이며 기존 사용자 프로필의 무손실 롤백,
Gstack 런타임, 모델 선택 또는 구독 청구 안전성의 증거가 아니다.

v18 Codex 격리 게스트 리허설(2026-09-28): 네트워크·클립보드·vGPU를
차단한 새 Windows Sandbox 사용자 프로필에서 Codex CLI 0.155.0 실행
파일과 `codex-overlay-v18`만 읽기 전용으로 매핑했다. 게스트 인증정보는
없었다. 로컬 marketplace 5개 등록, 플러그인 5개 설치·활성 뒤 캐시
737파일의 상대 경로·크기·SHA-256이 오버레이 영수증과 전부 일치했다.
시험 게스트에서 플러그인과 marketplace를 모두 철회하자 해당 목록과
캐시 파일이 각각 0개였고, 게스트 세션은 종료했다. 오버레이 digest도
전후 재검증했다. 원시 결과와 실행 스크립트는
`E:/Coding Infra/Releases/SimonK-stack/20260928-v18-codex-sandbox-probe/`에
있다. 이는 **새 게스트의 로컬 설치·바이트 복사·철회** 증거이며 기존
사용자 Codex 프로필 롤백, 실제 스킬 실행·훅, Gstack 런타임 또는
구독 청구 안전성의 증거가 아니다.

후보 manifest의 `runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 모두 `false`다. 실제 모델 선택·안전 훅·Bot/Orca
연결·전체 182스킬 동작, 구독 청구 안전성, 사용자 홈 롤백은 이 빌드가
증명하지 않는다. 사용자 설치·`main` 머지·결제 설정 변경·모델/API/Bot
실호출은 수행하지 않았다.

## v19 Stack 평가 스키마 검증 후보 (2026-09-28)

원본 SimonKStack 기능 브랜치 `fix/skill-validation-260927`의 `7f866e7`은
기존 선택 트리거 배열 파일 6개와 행동 assertion 스키마 파일 25개를 각각 검증하는
오프라인 CI 단계를 추가했다. 평가 파일이 없는 27개 스킬은 숫자로 보고하지만
이 검사는 모델 선택 정확도나 실제 스킬 동작을 실행하지 않는다. v18에 적용한
Core 공통 평가 스키마의 `invalid` 6건은 서로 다른 레거시 스키마였으므로
잘못된 케이스로 고쳐 쓰지 않았다. Stack README는 Core 동반 설치를 권장하고
`skstack`은 Core·Design 스킬이 없을 때 기능을 축소한다고 명시한다.

SimonK-stack 기능 브랜치의 `distribution/plugin-inputs.v1.json`을 새 Stack
커밋으로 핀했다. 새 `.gitignore`를 공식 루트 구성요소로 분류하도록
`plugin_bundle.py`를 확장하고 회귀 테스트를 추가했다. 초기 Windows 로컬
복제본은 Git의 CRLF 체크아웃 때문에 후보 검증에서 거절됐다. 원본·v18은
변경하지 않고 `core.autocrlf=false`인 별도 로컬 복제본으로 다시 빌드했다.
격리 산출물은
`E:/Coding Infra/Releases/SimonK-stack/20260928-v19-eval-schema/`에 있다.

| 산출물 | 검증 digest | 범위 |
|---|---|---|
| 재빌드한 `source-v19` | `9f1abd11fa3b648fe12ed1dc78183881e236d957bde007002cda61ece69567f8` | v18 소스와 동일 digest·137스킬·409파일 |
| `candidate-safety-v19` | `14bce7604f30190d2921de751c4f44687097890241cf80a06669b41defd33593` | 5플러그인·182스킬·734파일 |
| `codex-overlay-v19` | `2bc9a908ea08057165a6680a208181206ce353b6dd1bedd31ee7c214aea81a71` | Codex 호환 manifest 추가 |

후보 빌드에는 먼저 검증한 동일 digest의 `source-v18`을 사용했고, 현재
기능 브랜치에서 `source-v19`를 독립 재빌드해 소스 digest 동일성을 확인했다.
v18 대비 후보 추가 파일은 Stack `.github/validate-evals.mjs`, 그 단위테스트,
`.gitignore`의 세 개이고 변경 파일은 Stack CI workflow와 README 두 개다.
스킬 payload 변경은 0개다. 패키저 회귀 45개, 영수증 재검증과 격리 후보
`/vibe` smoke 4단계, Codex overlay 5개 회귀 테스트가 통과했다.
정적 경로 감사는 182스킬의
경로 142곳에서 미해결·비이식 명령 0건을 확인했으나 Gstack 외부 런타임
참조 31스킬·646문자열·9대상 때문에 예상대로 종료 1이다.
`runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 모두 `false`로 유지한다. 사용자 설치본·운영
marketplace·`main`·결제 설정·모델/API/Bot 실호출은 변경하지 않았다.

## v20 모델 근거 및 격리 설치 리허설 (2026-09-28)

기능 브랜치 `feat/skill-context-budget-260925`의 `ee40afb`는 최신 공식
모델 근거를 재검증하고 `/vibe` 중앙 레지스트리의 관측 시각을 갱신했다.
`candidate-safety-v20`은 5플러그인·182스킬·734파일이며 digest는
`9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`이다.
Codex 오버레이 digest는
`08f85de1b88eff8e3057aa0139eca46cea28094aa9a450b5be6814edd32992c8`이다.

최신 후보를 네트워크·클립보드가 꺼진 Windows Sandbox의 새 무인증
프로필에서 호스트별로 설치·철회했다. Claude Code 2.1.283은 5개
플러그인 설치·활성, 캐시 734파일의 상대 경로·크기·SHA-256 일치,
철회 후 설치·marketplace 각 0개를 확인했다. CLI가 남긴 게스트 캐시
739파일은 구성 항목을 이번 시험에서 목록화하지 않았고 직접 삭제하지 않았다.
Codex CLI 0.155.0은 5개 설치·활성, 오버레이 캐시 740파일 전부 일치,
철회 후 설치·marketplace·캐시 각 0개를 확인했다. 양쪽 후보와 CLI
실행 파일은 읽기 전용으로 매핑했고, 테스트 게스트는 결과 수집 후 닫았다.
원시 JSON·스크립트·Sandbox 설정과 해석 범위는
`E:/Coding Infra/Releases/SimonK-stack/20260928-v20-install-rehearsal.html`에 있다.

별도 Gstack 시작 절차 검사에서는 고정 원본 `01593aa6`의 Claude·Codex
생성 문서 62개 조합 중 존재하는 시작 절차 55개가 네트워크 차단
게스트에서 통과했다. 생성 문서 부재 3개와 시작 절차가 없는 문서 4개가
있고, Claude `health`는 첫 30초 제한을 넘긴 뒤 60초 재시험에서
통과했다. 상세 증거는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-batch-sandbox/report.html`에 있다.

고정 원본의 종료 경로도 별도 무인증·네트워크 차단 Sandbox에서
`qa`·`retro`·`ship` 세 대표 스킬로 검사했다. 각각 시작 스크립트가
출력한 세션 ID·시작 시각을 종료 스크립트에 전달했고,
`gstack-brain-sync --discover-new`·`--once`를 포함한 네 호출이 모두
종료 0이었다. `update_check=false`, `telemetry=off`,
`artifacts_sync_mode=off`에서 게스트 텔레메트리 파일·동기화 큐 항목·
프로젝트 Git 변경이 없었다. 원시 자료와 범위는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-end-sandbox/report.html`에
있다. 이것은 31개 legacy 스킬의 동작 또는 네트워크가 있는 호스트의
송신 안전성 증거가 아니다.

패키징 크기 참고값: v20 후보 영수증 734파일 합계 5,550,913바이트와
고정 Gstack Git 트리 2,821 blob 합계 58,741,859바이트를 단순 합하면
64,292,772바이트로 현 64 MiB 파일 합계 상한보다 2,816,092바이트
작다. `bin`·`lib`·`scripts` 및 일부 루트 파일 299개 합계는
13,018,800바이트다. 둘 다 **빌드/전이 의존성 폐쇄 증거가 아니다**.
특히 Git 트리에 없는 네이티브 CSO·컴파일 산출물과 외부 Bun 의존성,
기존 홈 링크 문제가 남는다. 크기만으로 Gstack 복사·설치를 결정하지 않는다.

Claude Code 2.1.283의 별도 `--init-only` 검사는 새 무인증·네트워크 차단
Sandbox에서 대조군과 5플러그인 후보 모두 실제 CLI 종료 코드 0이었다.
후보 로그는 플러그인 5개, 스킬 182개(중복·사용자 소유 제외 0개), 명령
5개 로딩과 디버그 오류 0개를 기록했다. 처음 시도는 `Start-Process`
객체의 빈 `ExitCode`를 실패로 오판했으므로 종료 판정에서 제외하고,
게스트 안에서 직접 호출한 `$LASTEXITCODE`만 판정에 썼다. 원시 출력,
스크립트, 격리 설정과 해석 경계는
`E:/Coding Infra/Releases/SimonK-stack/20260928-v20-claude-init-probe/report.html`에 있다.

이 시험들은 빈 게스트의 복사·등록·초기화·시작 절차 일부를 검증한 것일 뿐,
기존 사용자 프로필의 무손실 갱신·복원, 전체 스킬 동작, 훅, Gstack
외부 런타임 폐쇄, Windows CSO, Bot/Orca 연결, 모델 선택이나 구독 청구를
입증하지 않는다. 따라서 `runtime_closure_verified`,
`host_compatibility_verified`, `installation_ready`는 모두 `false`이고
사용자 설치본과 원본 `main`은 변경하지 않았다. 모델/API/Bot 실호출과
결제 설정 변경도 없었다.

### 고정 Gstack 원본의 패키징 적합성 감사

`scripts/gstack_source_inventory.py`는 **별도 격리된** Gstack Git 복제본의
고정 커밋, tree/index와 실제 작업 파일을 읽기 전용으로 대조하고
원시 바이트의 SHA-256 영수증을 산출한다. 사용자 홈의 설치된 Gstack을
읽거나 변경하지 않는다.

```powershell
python -B scripts/gstack_source_inventory.py --source-root E:/reviewed/gstack --expected-commit <검토한-40자리-SHA>
```

출력의 `package_contract_compatible`은 현재 파일형식·크기 한도에 관한
정적 판단만 뜻한다. 독립 복제본 `01593aa67c94780528e8f5121e47362502410ced`는
2,821개 Git blob 중 `connect-chrome` 한 개가 mode `120000` 심볼릭 링크여서
`unsupported_git_modes`로 차단됐다. Windows가 이를 일반 파일로 풀어도
Git 원본 모드 기준으로 차단한다. 이 원본 전체를 링크 금지 계약에 그대로
실을 수 없으며, 별도 소유권·별칭 변환 결정과 전이 helper 검증이 필요하다.
관측한 tree OID는 `cef8a713eda67e50d8b8519eabefdd7590c76262`, 원시
영수증 SHA-256은 `3b7818644e421635631ca08e6cbd374c821653de98e4fb359822f51ae009f77b`다.
영수증은 서명, 실행 가능성, 모델·호스트·구독 과금 증명이 아니므로
`runtime_closure_verified`와 `installation_ready`는 계속 false다.

### 직접 참조 Gstack helper 9종의 격리 실행

고정 원본의 `bin/gstack-config`, `gstack-slug`, `gstack-repo-mode`,
`gstack-learnings-log`, `gstack-learnings-search`, `gstack-timeline-log`,
`gstack-telemetry-log`, `gstack-update-check`, `gstack-team-init`을
네트워크·인증정보 없는 Windows Sandbox의 새 임시 Git 프로젝트에서
각각 실행했다. 호스트 원본·Git·Bun은 읽기 전용으로 매핑했다. Bun이
읽기 전용 공유 폴더의 TypeScript 모듈을 열 때 `EPERM`을 반환했으므로
`bin`·`lib`·`VERSION`을 **게스트 내부**에 복사하고 9개 helper 바이트를
원본과 재대조했다. JSON 인자는 고정 Bash fixture로 전달했다.

최종 실행은 9/9 통과했다. `update_check=false`, `telemetry=off`,
`artifacts_sync_mode=off`에서 활성 네트워크 어댑터 0, 동기화 큐 파일 0,
텔레메트리 파일 0이었다. 학습 1건 기록·검색과 타임라인 1건 기록은
게스트 상태 폴더 안에서 이뤄졌다. `gstack-team-init optional`은
vendored Gstack이 **없는** 게스트 프로젝트의 `CLAUDE.md` 하나만 만들었고
커밋은 하지 않았다. 세 번의 실패 시험과 최종 원시 결과·스크립트는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-nine-helper-sandbox/`에
보존했다.

이 결과는 지정 입력·설정의 직접 helper 경로에 한정된다. 기본 설정의
네트워크·동기화, `gstack-team-init`의 vendored 폴더 삭제 분기,
31개 스킬의 전이 실행 의존성, GUI/CSO 빌드, 기존 사용자 설치본 및
구독 청구를 검증하지 않았다. 세 readiness 플래그는 여전히 false이며
사용자 설치본·원본 `main`·결제 설정을 변경하지 않았다.

### Gstack 원본 `setup`의 오프라인 설치 경계

같은 고정 원본 `01593aa`의 `setup`을 읽기 전용으로 추적했다. `--local`은
Claude 전용이며 Codex에서는 거부된다(`setup:670–686`). 이 옵션도
`gstack-migrate-claude-code` 호출(`setup:1070–1083`), 빌드 산출물 검사와
필요 시 `bun install --frozen-lockfile` → 일반 `bun install` fallback 및
`bun run build`(`setup:1090–1129`), Claude 스킬 등록 전의 생성 단계들을
건너뛰는 **무변경 dry-run 옵션이 아니다**. `--no-team` 역시 팀 훅 등록
선택이지 이 선행 작업의 생략 조건이 아니다. Windows 복사 helper는 대상
삭제 뒤 재복사할 수 있고(`setup:280–299`), 사용자 소유권 판정·백업
경로가 있는 실제 설치기이므로 기존 프로필에 시험 삼아 실행하지 않는다.

고정 원본 작업트리에는 `node_modules`, `browse/dist/browse.exe`,
`design/dist/design.exe`, `make-pdf/dist/pdf.exe`,
`browse/dist/.build-complete`, `bin/gstack-global-discover.exe`,
`bin/gstack-cso-launcher.exe`가 모두 없다. 따라서 **이 입력만으로**
네트워크 차단 게스트에서 `setup`의 빌드·설치 성공을 기대할 수 없으며,
앞의 helper 9/9 결과를 전체 설치 리허설로 승격할 수 없다. 일반 빌드는
공개 패키지 의존성과 플랫폼별 생성물의 고정 입력·영수증·빌드 검증이
선행돼야 한다. 이는 유료 모델 호출 필요성을 뜻하지 않는다. 패키징
범위·별칭 소유권·롤백 계약은 허브 §35 결정 이후 확정한다. 이번 점검은
`setup`을 실행하지 않았고 사용자 설치·결제·readiness 플래그를 바꾸지 않았다.

### 고정 Gstack의 격리된 프로젝트 로컬 설치

별도 네트워크 사용 Windows Sandbox의 **새 프로젝트·새 HOME**에서 위
`01593aa`를 읽기 전용 매핑 후 게스트 내부 Git clone으로 복사했다. Bun도
SHA-256 대조 후 게스트 내부로 복사했고, 모델/API 인증정보는 전달하지
않았다. `telemetry=off`, `update_check=false`, `artifacts_sync_mode=off`,
`auto_upgrade=false`를 먼저 설정했다. 공개 Bun 패키지 다운로드를 허용하되
`GSTACK_SKIP_PLAYWRIGHT=1`로 Chromium bootstrap은 생략했다. 프로젝트
루트에서 다음 명령을 실행했다.

```bash
bash .claude/skills/gstack/setup --local --host claude --no-team \
  --prefix --no-plan-tune-hooks --no-timeline-stop-hook --quiet
```

최종 게스트에서 `setup` 종료 0, `browse`·`design`·`make-pdf`·
`gstack-global-discover` Windows 실행 파일과 빌드 스탬프 존재,
프로젝트 `.claude/skills`의 `SKILL.md` 보유 엔트리 57/57을 확인했다.
구성은 로그의 `linked skills` 54개와 `gstack`, `_gstack-command`,
`gstack-connect-chrome` 세 엔트리다. `gstack-qa`, `gstack-cso`,
`gstack-open-gstack-browser`, 이름 재작성된 `gstack-connect-chrome`도
실제 경로 검사를 통과했다. 원본 clone의 추적 파일 53개는 생성·이름
패치로 변경됐으므로 이 설치 절차를 불변 패키지 입력에 직접 적용할 수
없다. 원격 Gstack HEAD와 호스트 고정 원본은 같은 commit이며 호스트
작업트리는 깨끗하다.

첫 두 번의 `setup` 종료 0은 **시험 하네스의 작업 디렉터리 오류**로
프로젝트가 아닌 Gstack 소스 내부의 중첩 `.claude/skills`에 등록됐다.
그 결과 프로젝트 엔트리는 `gstack` 하나였으며 성공 판정에서 제외했다.
명령을 프로젝트 루트로 수정한 세 번째 독립 게스트의 `output3/`만 위
57/57 판정의 근거다. 첫 두 출력도 오류 이력으로 보존했다. 자체완결
보고서와 결과 JSON·하네스는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-setup-sandbox/`에 있다.

생성 과정의 Codex-format `gstack-plan-ceo-review`·`gstack-ship` 문서는
원본 생성기의 160,000바이트 token-ceiling 경고를 받았다. 이 경고는
Codex 호스트가 실제 거절했다는 측정은 아니다. 이번 결과도 Gstack **단독
Claude 프로젝트 로컬 설치**와 실행 파일 생성만 증명한다. Playwright,
Windows CSO 네이티브 launcher, 5플러그인 동시 설치, 기존 사용자 프로필
롤백, 스킬 본문 전이 실행, 구독 청구 안전성은 검증하지 않았다. Gstack을
현 8 MiB/64 MiB 후보 영수증에 자동 포함하거나 세 readiness 플래그를
올리지 않는다. Sandbox는 출력 보존 후 종료했고 사용자 설치본·`main`·
결제 설정·모델/API/Bot/Orca 호출은 변경·실행하지 않았다.

### Gstack 프로젝트 스킬과 v20 플러그인 동시 초기화

위 로컬 설치 하네스를 새 Windows Sandbox에서 다시 실행하고,
`postcheck.json`의 프로젝트 Gstack 엔트리 57/57을 통과 조건으로 삼았다.
같은 게스트에서 Claude Code 2.1.283의 `--init-only`를 두 번 실행했다.
첫 번째는 Gstack 프로젝트만, 두 번째는 검증된
`candidate-safety-v20`의 5개 플러그인을 각각 `--plugin-dir`로 추가했다.
Gstack 원본은 `01593aa67c94780528e8f5121e47362502410ced`, 후보
영수증 SHA-256은
`9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`
로 고정했다. 게스트에는 모델/API 인증정보를 넣지 않았고 모델 응답 생성은
실행하지 않았다. 공개 Bun 패키지 다운로드를 위해 네트워크 어댑터 1개가
활성화됐으며, Gstack 설정의 telemetry/update/sync/auto-upgrade는 꺼져
있었다.

두 초기화 모두 종료 0이었다. 첫 실행은 프로젝트 스킬 57개,
플러그인 0개를 로딩했고, 합동 실행은 같은 프로젝트 스킬 57개와
플러그인 스킬 182개·5개 플러그인을 로딩했다. 합동 실행에서
`duplicate/user-owned entries skipped`는 0, 디버그 `[ERROR]`도 0이었다.
첫 **단독** 실행에는 새 게스트의 아직 없는 `.claude.json` 잠금 저장
시도에서 `ENOENT` 디버그 오류 1건이 있었으므로 무오류 실행으로
기록하지 않는다. 합동 실행에는 같은 오류가 재발하지 않았다. 원시
영수증·로그·하네스와 자체완결 보고서는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-v20-coexistence/`에
보존했다.

이것은 Gstack **프로젝트 로컬** + v20 `--plugin-dir` 임시 로딩의
**초기화 공존** 증거다. 5플러그인의 실제 marketplace 설치·철회,
기존 사용자 프로필과의 호환, 31개 참조 스킬의 실행·전이 의존성,
Playwright/CSO, 모델·Bot·Orca 및 구독 청구는 포함하지 않는다.
따라서 원본 `main`, 사용자 설치본과 세 readiness 플래그는 그대로다.

### 격리 게스트 홈 Gstack 경로와 v20 후보 공존

프로젝트 로컬 검사는 후보 스킬 31개의 `~/.claude/skills/gstack/bin/...`
직접 참조를 증명하지 못한다. 이를 구분하기 위해 **새** Windows Sandbox의
`C:/guest-home/.claude/skills/gstack`에 같은 고정 원본
`01593aa67c94780528e8f5121e47362502410ced`을 복제하고,
`setup --host claude --no-team --prefix`를 게스트에서 실행했다. 사용자 홈의
설치된 Gstack은 마운트·열람·변경하지 않았다. 게스트에는 인증정보를
전달하지 않았고, Gstack telemetry/update/sync/auto-upgrade는 꺼두었다.
공개 Bun 의존성 설치를 위한 게스트 네트워크만 허용했다.

설치 종료 0, 게스트 홈 스킬 엔트리 57개, 직접 참조 helper 9/9 파일이
존재했다. 게스트 Bash에서 후보가 쓰는 `$HOME/.claude/skills/gstack/bin/`
경로의 `gstack-config get telemetry`가 종료 0·`off`를 반환했다. 같은
게스트의 Claude Code 2.1.283 `--init-only`는 Gstack 단독과 v20 후보
5개 플러그인 동시 로딩 모두 종료 0이었다. 단독은 user 스킬 57개,
합동은 user 스킬 57개 + 플러그인 스킬 182개/5개 플러그인,
duplicate/user-owned skip 0, 합동 디버그 오류 0이었다. 첫 단독
초기화에는 아직 없는 게스트 `.claude.json`의 lock-save `ENOENT`
디버그 오류 1건이 있었고 합동 초기화에는 재발하지 않았다.

원시 영수증·로그·하네스·보고서는
`E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-home-v20-probe/`에
있다. 이는 **격리 게스트의 홈 경로·초기화 공존**만 증명한다. 31개 스킬
본문 전이 실행, 실제 사용자 홈 설치·롤백, marketplace 전환, 모델 호출,
구독 청구 안전성은 검증하지 않았다. 세 readiness 플래그는 올리지 않고
기존 `main`·사용자 설치본·결제 설정을 유지한다.

### 기존 항목이 있는 격리 프로필의 후보 철회

빈 게스트만으로는 기존 사용자 항목의 보존을 판정할 수 없어, **새 무인증·
네트워크 차단 Sandbox 두 개**에 각각 무관한 시험 플러그인과 개인
`SKILL.md`를 설치한 후 v20 후보 5개를 추가·철회했다. Claude 게스트에는
기존 설정의 `env` 표식도 넣었다. 보호 대상 플러그인의 캐시 파일 전체
상대경로·SHA-256과 개인 스킬 해시를 설치 전후 대조했다. 실제 사용자
프로필·인증정보는 게스트로 복사하지 않았다.

Claude Code 2.1.283은 설치 중 플러그인 6개, 철회 후 기존 시험 플러그인
1개/marketplace 1개를 유지했다. 보호 대상 캐시 3개 파일의 해시 차이
0건, 개인 스킬 해시 동일, 설정 표식 `keep`, 기존 플러그인 enabled였다.
그러나 **후보 캐시 파일 739개가 철회 후에도 남았다**. 기존 무관한 항목
보존은 입증했지만 설치 전 프로필 바이트 상태로의 완전 복원은 아니다.

Codex CLI 0.155.0도 설치 중 플러그인 6개, 철회 후 기존 시험 플러그인
1개/marketplace 1개 enabled를 유지했다. 보호 대상 캐시 4개 파일의
해시 차이 0건, 개인 스킬 해시 동일, 후보 캐시 잔여 0개였다. 최초
Codex 시도는 시험 플러그인 manifest 결손으로 후보 설치 전에 중단됐고,
중간 성공 시험은 출력 이름 필드가 null이었다. 두 영수증을 보존하고
manifest/출력 필드를 고친 **최종 새 게스트 결과**만 판정에 사용했다.

양쪽의 원시 JSON·재현 스크립트·Sandbox 정의와 자체완결 보고서는
`E:/Coding Infra/Releases/SimonK-stack/20260928-existing-profile-rollback/` 및
`E:/Coding Infra/Releases/SimonK-stack/20260928-existing-codex-profile-rollback/`에
있다. 이 시험은 **합성 기존 항목**을 가진 격리 프로필의 보존 범위다.
실제 사용자 프로필의 상태·충돌·복원과 전체 스킬 행동을 입증하지
않는다. 특히 Claude 잔여 캐시를 실제 홈에서 자동 삭제하지 않는다.
readiness 세 플래그와 사용자 설치본·`main`·결제 설정은 그대로다.

### 현재 PC의 flat 스킬과 v20 후보 중복·진입점 감사

`/vibe`의 실제 전환 경계를 찾기 위해 현재 PC에서 **내용 스캔을 허용한
네 flat 스킬 루트만** `inventory`로 읽고, 금지된 홈 Gstack 경로를
`--exclude-root`로 선제 제외했다. 결과는 선택된 이름 198개, 후보
182개와 교집합 138개였다. 후보와 선택된 설치본의 `SKILL.md` 원시
해시가 같은 이름은 `multi-terminal-dispatcher` 1개뿐이고, 137개는
다르며 44개는 이 범위의 설치본에 없다. `coverage`의 후보 플러그인
내용은 182개 모두 matched였다. 홈 inventory는 Gstack의 두 경로를
의도적으로 제외해 `scope_complete=false`이므로 전 PC 또는 호스트
네이티브 스킬 전체의 완전성 증거가 아니다. 이름 중복은 곧바로 런타임
충돌이나 선택 우선순위를 뜻하지 않는다.

현재 `.claude/skills`의 flat 핵심 진입점 5개(`vibe`, `vibe-bot`,
`simonk`, `model-router`, `multi-terminal-dispatcher`)는 모두
`20260926-selection-validation/candidate`의 Core 스킬로 향하는 정션이다.
Codex의 flat `vibe`·`vibe-bot`은 다시 이 `.claude/skills` 정션을
가리킨다. 현재 flat `vibe`는 2.11.6, v20 후보는 2.12.1이며 해시가
다르다. `vibe-bot`은 0.9.1→0.9.3, `model-router`는 0.2.1→0.2.4다.
Claude 플러그인 등록부에는 SimonK 0개(전체 설치 2개), Codex CLI
플러그인 목록에도 SimonK 0개(전체 활성 20개)였다. **플러그인만
설치하면 기존 flat `/vibe` 정션의 본문이 자동 교체된다는 증거는 없다.**

별도 무인증·오프라인 Sandbox에서 기존 flat 핵심 스킬 5개를 게스트
사용자 스킬로 복사하고 v20 5개 플러그인을 `--plugin-dir`로 동시에
초기화했다. Claude Code 2.1.283 두 실행 모두 종료 0, flat user 스킬
5개 유지, 플러그인 스킬 182개 로딩, duplicate/user-owned skip 0,
합동 디버그 오류 0이었다. 첫 flat-only 초기화에는 새 게스트
`.claude.json` lock-save `ENOENT` 디버그 오류 1건이 있었다. 이 결과는
양쪽 **등록 공존**을 증명하지만 `/vibe` 실제 호출이 어느 본문을
선택하는지는 증명하지 않는다. 새 후보 배포에는 flat 진입점 전환·
복원 설계와 실제 명령 선택 검증이 별도로 필요하다. 원시 영수증과
보고서는 `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-v20-priority-probe/`에
있다. 기존 정션·설치본·`main`·결제 설정은 변경하지 않았다.

### 핵심 flat 정션 5개의 격리 전환·역복원

위 복사본 시험은 새 후보로 정션 자체를 바꾸는 경우의 중복 처리를
측정하지 않는다. 이를 분리하려고 또 다른 **무인증·오프라인 Windows
Sandbox**의 새 `.claude/skills`에 구 후보를 가리키는 핵심 정션 5개를
만들고 `.codex/skills`의 `vibe`·`vibe-bot` 2개가 이를 재참조하게 했다.
이동 전에 구/신 본문 SHA-256과 정확한 게스트 경로를 적은 매니페스트,
별도 역방향 스크립트를 만들었다. 원본 정션은 guest archive로 옮기고
새 정션을 만들었다. 실제 사용자 홈이나 홈 Gstack은 매핑하지 않았고
삭제 명령도 쓰지 않았다.

전환 직후 Claude flat 5개와 Codex 경유 2개는 신 후보 SKILL 해시를
가리켰다. Claude Code 2.1.283의 `--init-only`는 user 스킬 5개와
플러그인 스킬 **177개**를 로딩했고 `duplicate/user-owned` **5개를
제외**했다. 즉 5+177=182개가 등록됐고 합동 디버그 오류 0,
초기화 종료 0이었다. 이전의 *구 후보 복사본* 공존 시험(플러그인
182개·제외 0)과 수치가 다른 것은 flat 정션이 **신 플러그인의 동일
경로**를 가리키는 경우에 한정된다. 디버그 로그는 제외된 플러그인
항목을 `simonk-core:model-router`, `simonk-core:multi-terminal-dispatcher`,
`simonk-core:simonk`, `simonk-core:vibe`, `simonk-core:vibe-bot`으로
명시한다. 이 다섯 스킬은 사용자 수준 flat 로더에 이미 노출됐다는
이유로 플러그인 로더가 건너뛴 것이다. 각 명령의 실제 런타임 선택과
`/vibe` 응답은 여전히 측정하지 않았다.

별도 역방향 스크립트로 구 정션 5개와 Codex 경유 2개의 구 본문 해시가
복원됐고, 신 정션은 삭제하지 않고 guest quarantine으로 옮겼다.
복원 스크립트를 한 번 더 실행해 같은 상태로 유지됨도 확인했다.
첫 게스트는 `plugin_skills=182/skip=0`이라는 잘못된 예상식 때문에
`incomplete`로 표기됐지만 정션·복원 관측 자체는 통과했다. 예상식을
`177/5`로 고쳐 새 게스트에서 최종 `pass`를 받았으며 두 영수증을
보존했다. 자료는
`E:/Coding Infra/Releases/SimonK-stack/20260928-flat-bridge-rollback/`에
있다. 이것은 **게스트 정션 전환·역복원 기계 검증**이지 실제 사용자
프로필 변경 승인이나 모델 실호출 검증이 아니다. Claude 소유권 D-code,
실제 명령 선택·설치 캐시 복원, 세 readiness 플래그는 열려 있다.

### flat 별칭 소유권의 후속 검토 (미결정)

[Claude Code 공식 스킬 문서](https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name)는
플러그인 스킬의 이름공간 명령과, 다른 명령과 충돌하지 않을 때의 짧은
명령을 구분한다. 위 격리 로그에서는 새 후보의 flat 정션 5개를 함께
제공하면 그와 동일한 파일의 `simonk-core:*` 항목 5개가 제외됐다.
반면 Claude flat 5개를 단순 철회하면 현재 그 정션을 재참조하는
Codex flat `vibe`·`vibe-bot` 2개가 끊길 수 있다. 별도 패널·독립 심판은
**Claude 플러그인 단독 + Codex 별도 고정 진입점**을 검토안으로 제시했다.
이는 허브 D-code나 실제 설치 승인이 아니며, 짧은/이름공간 명령의
실제 사용자 프로필 선택은 미측정이다.

이 구조의 추가 Windows Sandbox 시험을 두 번 기동했으나 둘 다 최초
게스트 부팅 마커조차 만들지 못했다. CLI 초기화·정션 전환 스크립트의
성패를 판정할 실행 증거가 당시에는 **없었다**. 자료는
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/`에
보존했다. 이전 격리 시험의 PASS를 이 새 구조의 PASS로 확장하지 않는다.
원인 분리를 위해 후보를 전혀 매핑하지 않은 2폴더 최소 Sandbox도
시도했다. `LogonCommand` 스크립트의 첫 동작을 출력 폴더에 마커 쓰기로
바꾼 재시험까지 마커가 없었다. 두 시험의 정확한 인스턴스만 종료했다.
따라서 새 스킬 코드 실패로 단정할 수 없으며, `.wsb` 실행의 Sandbox 시작·
명령 전달·폴더 매핑 경계 중 어느 지점인지도 확정하지 못했다.
자료는 `E:/Coding Infra/Releases/SimonK-stack/20260928-sandbox-boot-triage/`에
있다.

후속으로 [Microsoft의 Windows Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)의
`start`·`share`·`exec --run-as System`을 이용해 인스턴스 ID가 있는
새 무인증·네트워크 차단 게스트에서 명령을 직접 실행했다. 최소 2폴더
시험은 첫 마커·JSON을 만들었고 게스트 활성 네트워크 어댑터 0이었다.
정확한 인스턴스 ID를 `stop`으로 종료했다. 이는 앞선 `.wsb`의
`LogonCommand` 무출력 원인을 규명한 것은 아니지만, 동등한 격리
명령 실행 경로를 확보한 것이다.

같은 CLI의 별도 새 게스트에 구 후보·v20 후보·Claude 실행 파일·Git은
읽기 전용, 결과 폴더만 쓰기 가능으로 공유해 split bridge 전체
스크립트를 실제 실행했다. 첫 실행은 전환·복원 수치가 맞았으나
빈 게스트의 `.claude.json` 잠금 생성 `ENOENT` 디버그 오류 1건으로
`incomplete`였다. 게스트 내부에 빈 `{}` 설정을 사전 생성한 뒤
**또 다른 새 게스트**에서 재시험해 최종
`guest_plugin_only_split_bridge_passed`를 받았다. Claude Code 2.1.283
`--init-only` 종료 0, user 스킬 0·플러그인 스킬 182·중복 제외 0·
디버그 오류 0, Codex 신규 직접 정션 해시 2/2, Claude 구 flat 정션
복원 5/5, Codex 구 경유 정션 복원 2/2였고 역복원 재실행도 통과했다.
후보 digest는 `9b0980ae...ba1318`, 최종 게스트 매니페스트 SHA-256은
`E18CECF4...D50566`이다. 원시 결과·매니페스트·로그·스크립트는
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-rerun/`와
그 부모의 `input/`에 보존했다. 두 게스트 모두 모델 생성·유료 호출이
없었으며 정확한 시험 인스턴스만 종료했다.

이 PASS는 **격리된 새 프로필의 전환·로더·복원 범위**에 한정된다.
실사용 Claude `/vibe`·`/simonk-core:vibe`와 Codex 별칭의 명령 선택,
기존 호스트 프로필의 캐시·훅, 182개 스킬 전체의 동작과 외부 런타임
폐쇄는 입증하지 않는다. Claude 소유 D-code와 실제 설치 결정도
여전히 열려 있으므로 세 readiness 플래그는 false이고 사용자
설치본·원본 `main`은 변경하지 않았다.

호스트용 별도 사전 검사·역복원 스크립트도 또 다른 네트워크·인증정보
없는 새 Sandbox에서 검사했다. 게스트 내부에만 실제 호스트와 동일한
`C:/Users/202502/.claude`·`.codex` 경로 구조를 만들고, 후보를 읽기
전용으로 공유했다. 게스트에 맞게 후보 대상만 치환한 매니페스트로
`host-preflight.ps1`이 기존 7개 정션·구/신 본문 해시를 확인했고,
`host-rollback.ps1`은 제안한 전환 후 Claude 5개·Codex 2개를 원상
복원했다. 두 번째 역복원도 PASS였으며 새 Codex 정션 2개는 삭제하지
않고 격리 폴더에 보존했다. 영수증은
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-host-rehearsal/host-rollback-result.json`에
있다. 호스트용 스크립트의 로직을 게스트에서 확인한 것이며 실제
호스트 링크를 이동하거나 복원한 것은 아니다. 정확한 게스트 ID는
종료했고 현재 호스트 사전 검사도 PASS다.

세션 한정 `--plugin-dir`과 영속 로컬 marketplace 설치가 동일하다고
가정하지 않기 위해, 각각 새 Windows Sandbox에서 **플러그인 설치 +
flat 별칭 분리 + 복원·철회**를 결합 시험했다. Claude 게스트는 후보
5개를 로컬 marketplace에 등록·설치한 뒤 구 Claude flat 5개를
보관하고 Codex 경유 2개를 v20 직접 정션으로 바꿨다. 플러그인 설치
목록 5개, `--plugin-dir` 없이 `--init-only` 종료 0, user 스킬 0·
플러그인 스킬 182·중복 제외 0·디버그 오류 0이었다. 링크 복원 5+2개와
역복원 재실행이 통과했고 플러그인 철회 뒤 설치 목록은 0개였다.
첫 시도는 빈 JSON 객체의 속성을 PowerShell이 `null` 1개로 센 시험
판정식 오류로 `incomplete`였으며, 같은 게스트의 원시 설치 목록은
비어 있었다. 판정식을 고친 **새 게스트**의 최종 영수증은
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-integrated-rerun/integrated-result.json`이다.

별도 Codex 게스트는 v20 Codex 오버레이 digest `08f85de1...32992c8`의
로컬 플러그인 5개를 설치·활성화하고 Core v20에 직접 연결된 flat
`vibe`·`vibe-bot` 2개가 SKILL 해시와 일치함을 확인했다. 분리 중에도
플러그인 5개 enabled였고, 구 Claude 5개·Codex 2개 정션 복원과
역복원 재실행 뒤 설치 목록은 0개였다. 영수증은
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-codex-integrated/codex-integrated-result.json`이다.
두 최종 시험은 인증정보·활성 네트워크 어댑터 없이 모델 생성·유료 호출
0건으로 수행했고 정확한 Sandbox ID를 종료했다. 이 결과도 각 CLI의
실제 `/vibe` 선택, 기존 호스트 사용자 설정·캐시, 훅·182스킬 실행,
구독 청구와 운영 설치 준비를 증명하지 않으므로 세 readiness 플래그와
실사용 설치·`main` 상태는 바꾸지 않는다.

호스트 복원 스크립트는 Codex 구 정션을 보관한 직후 새 정션 생성이
실패한 중간 상태도 처리하도록 보완했다. 또 다른 새 Sandbox에서
정상 전환·복원과 재실행 뒤, Claude `model-router` 및 Codex `vibe`의
구 정션만 보관하고 새 링크는 만들지 않는 부분 실패를 주입했다.
`host-rollback.ps1`이 두 링크를 원상 복구했고 최종 5+2 해시 검증이
통과했다. 영수증은
`E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-host-partial/host-rollback-result.json`에
있다. 실제 사용자 홈 링크는 변경하지 않았고 게스트는 종료했다.

기능 브랜치의 최신 문서 반영 상태에서 소스 스킬 품질 141/141,
Node 플러그인 검증 68스킬, 오프라인 benchmark 회귀 19건 및 후보
경로 감사 회귀 18건이 다시 통과했다. `origin/main`은 이 기능 브랜치의
조상이라 fast-forward가 가능한 그래프지만,
필수 D-code와 실사용 선택·readiness 검증 없이 `main`을
이동하지 않는다.

### Grok Bot 조직 스냅샷과 v20 후보 재대조 (2026-09-28)

사용자 제공 `grok-bot-org-overview-2026-09-24.md`의 SHA-256은
`3dbaba9585ecf01cdef216dae0eb74b367f4ac10e3d0e4bd8b2e83c9c8592dd3`로,
`vibe-bot/references/relay-charter.md`와 `bots.json`에 고정된 원본과
일치했다. 문서의 봇 19개와 팀 6개의 ID 25개는 v20 후보 명단과
양방향 누락 없이 일치한다. 설치 중인 봇 명단도 후보와 같은 해시지만,
설치 중인 `SKILL.md`는 0.9.1이고 v20 후보는 0.9.3이다.

v20 후보에서 외부 프로세스·네트워크 차단을 먼저 건 테스트 27건
(`test_execute_bot.py`)과 11건(`test_bus_watch.py`), 같은 차단을 건
`selftest.py` 93개 점검이 모두 통과했다. `web-qa`는 독립 프로필이
확인되지 않은 Relay 분류로 유지하고, 실제 봇 활성 상태·계정·구독
비용·수신 여부는 이 원본 문서와 오프라인 테스트에서 추론하지 않는다.
과제 전달·봇 실호출은 수행하지 않았고 사용자 설치본, 준비 플래그,
`main`은 바꾸지 않았다.

같은 날 현재 호스트의 Claude Max `claude.ai` 인증과 API 키 환경변수 부재를
확인한 뒤, `--setting-sources project,local`과 임시 `--plugin-dir`로
Core v20만 초기화했다. 종료 0, 사용자 스킬 0·
Core 플러그인 스킬 61·중복 제외 0이었다. 이어 Sonnet 5/low로
**명시적인** `simonk-core:vibe` Skill 호출 1회를 수행했고, 로컬 세션
기록에 `Skill` 도구 입력이 남았다. 초기화 목록에는 계정 연결 MCP 도구도
보였지만, 기록상 실행 도구는 `Skill` 1회였다. 응답은 이름을 맞췄지만 Skill 도구가
전달한 본문에서 frontmatter 버전을 관측하지 못했다고 답했다. 후보
파일의 버전은 별도 정적 확인상 2.12.1이다. 따라서 후보 명시 호출은
관측됐으나 자연어 자동 선택, 본문 전체 이해, 다른 스킬, 실제 작업
오케스트레이션은 검증되지 않았다. CLI의 `total_cost_usd`는 내부 사용량
추정치이지 실제 추가 청구 영수증이 아니며, 후속 모델 호출은 중지했다.
계정·자동충전 설정을 변경하지 않았고 세 준비 플래그는 false다.

### v20 legacy Gstack 시작 절차의 격리 일괄 실행 (2026-09-28)

후보 digest `9b0980ae...ba1318`의 Gstack `bin/` 참조 스킬 31개를
고정 원본 `01593aa67c94780528e8f5121e47362502410ced`와 함께 새
Windows Sandbox에 읽기 전용으로 매핑했다. 게스트는 활성 네트워크
어댑터 0개·인증 환경변수 없음이었고, 사용자 홈 Gstack은 연결하지 않았다.
각 스킬에서 `## Preamble (run first)`의 첫 Bash 블록을 추출해 `bash -n`과
실행을 검사했다. 30개가 구문·실행 종료 0 및 `BRANCH`·`REPO_MODE`·
`TELEMETRY: off` 표식을 통과했고, `gstack-upgrade` 1개는 해당 preamble이
없어 별도 분류했다. 31개 결과 행은 모두 고유하고 출력 로그의 명령 누락·
권한 오류 패턴은 0건이었다. 후보 receipt digest는 실행 전후 같았다.
결과 영수증은
`E:/Coding Infra/Releases/SimonK-stack/20260928-legacy-gstack-preamble-sandbox/output/result.json`
(SHA-256 `ee5645f6c42d577769b516bd0555a366daf65ab3da7b6167510cecb1060287d1`),
입력 스크립트와 개별 결과는 같은 부모의 `input/`·`output/`에 있다.
정확한 시험 Sandbox ID를 종료했고 남은 실행 인스턴스는 0개다. 이는
**legacy 시작 절차**의 격리 호환성이지 본문 작업·CSO 네이티브 빌드·
동적 의존성·실사용 Gstack 설치본 또는 Codex 훅 실행의 증거가 아니다.

### v20 후보 Gstack 시작 절차의 실제 타임라인 확인 (2026-09-28)

위 legacy 시험의 종료 코드만으로는 `|| true`가 가린 helper 실패를
구별할 수 없었다. 같은 digest의 **v20 후보**에서 `gstack/bin/`을 직접
참조하는 스킬 31개를 다시 골라, 새 Windows Sandbox의 게스트 전용 홈과
프로젝트 상태에서 시작 절차를 각각 실행했다. Gstack 고정 원본
`01593aa67c94780528e8f5121e47362502410ced`의 `bin/`·`lib/`·`VERSION`
파일 195개를 게스트로 복사해 SHA-256으로 대조했고, 사용자 홈 설치본·인증 파일은
연결하지 않았다. 시작 절차가 있는 30개는 모두 구문 검사·종료 0에
더해 **각각 실제 `timeline.jsonl` 1개 생성**을 확인했다.
`gstack-upgrade` 1개는 시작 절차가 없어 실행 대상에서 제외했다.
별도 새 게스트에서 31개를 재실행해 각 타임라인의 단일 JSON 이벤트가
해당 스킬의 `started`와 정확히 일치하는 것도 30/30 확인했다.
호스트 재대조에서 결과표의 30개 스킬 키와 이벤트 키가 같고 타임라인
SHA-256이 모두 고유했다. 이 2차 영수증은 같은 부모의 `output-events/`에
있으며, 이벤트 본문 확인을 포함하지 않은 최초 결과를 대체하지 않고 보강한다.

최종 게스트 사후 검사에서 활성 네트워크 어댑터·텔레메트리 파일·
동기화 큐 파일은 각각 0개였고, 후보 digest는 실행 전후
`9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`로
일치했다. 검증 도구와 원본 결과는
`E:/Coding Infra/Releases/SimonK-stack/20260928-candidate-gstack-preambles/`의
`input/`·`output-final/`에 있으며, 이전 탐색 실행은 별도 출력 폴더에
보존하고 최종 증거에 합산하지 않는다. 이 결과는 **30개 시작 절차의
동적 생성물**만 증명한다. 스킬 본문 전체 작업, 호스트 설치본과의
호환성, 모델·Bot 동작 및 전이 런타임 폐쇄는 아직 검증되지 않았다.
`runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 계속 `false`다.

또한 실제 호스트의 모델 생성 없는 Core v20 초기화에서
`--strict-mcp-config --mcp-config '{"mcpServers":{}}'`를 지정하면 사용자
스킬 0·Core 플러그인 스킬 61·중복 제외 0인 채 계정 MCP 원격 목록 조회가
디버그 로그에 나타나지 않았다. 앞선 기본 초기화에는 이 조회가 있었다.
이는 후속 선택 평가의 도구 범위를 줄이는 재현 가능한 옵션이지,
이미 수행한 실호출의 도구 목록을 소급 변경하거나 모든 외부 접근을
차단했다는 증거는 아니다. 추가 모델 호출·추가 과금·사용자 설치 전환은
이 단계에서 수행하지 않았으며 세 준비 플래그는 false다.

### Codex v20 오버레이의 `/vibe` 발견 경계 (2026-09-28)

v20 Codex 오버레이의 다섯 `.codex-plugin/plugin.json`은
`plugin-creator` 형식 검사를 각각 통과했다. 그러나 이 오버레이 내부의
`vibe/scripts/orchestrate.py catalog` 기본 호출은
`Candidate skill metadata differs from receipt`/종료 2로 닫힌다.
오버레이가 `zoom-out/SKILL.md`를 투영했지만 원본 `bundle.json`은
원본 바이트 영수증 그대로이기 때문이다. 182개 스킬 해시 중 불일치는
이 파일 1개다. 이 실패를 원본 후보 변조나
스킬 누락으로 해석하지 않는다. 고정된 오버레이 digest
`08f85de1b88eff8e3057aa0139eca46cea28094aa9a450b5be6814edd32992c8`
로 `scripts/codex_overlay.py verify`를 먼저 실행하면 종료 0이고,
그 뒤 다섯 `plugins/<owner>/skills` 경로를 **명시적 `--root`**로 준
`orchestrate.py inventory`는 182개 레코드·`status=complete`·종료 0이다.
명시적 루트 인벤토리는 별도의 오버레이 바이트 검증을 대신하지 않으며,
검증 후 후보 경로를 단일 작성자로 고정해야 한다. 이 조합은
`catalog` 기본 경로의 영수증 결합이나 실제 모델 선택·설치 호환성을
증명하지 않는다. 운영용 기본 카탈로그와 설치 전환은 여전히 보류한다.

2026-09-28 **병합 전 오프라인 회귀**: 기능 브랜치에서
`python -B -m unittest discover -s scripts/tests -p 'test_*.py'`는
311건 중 308건 통과·3건 후보 환경변수 부재로 건너뜀, 실패 0이었다.
v20 후보를 digest `9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`
로 다시 검증한 뒤 그 3건을 고정 후보 경로·digest를 제공해 별도로 실행했고
모두 통과했다. 모델 대신 임시 `claude.cmd`를 사용하는 시험이며 실호출은
없었다. 다섯 원본 플러그인 기능 브랜치는 각각 당시 `origin/main`을
조상으로 포함하고 원격 기능 브랜치와 동기화된 깨끗한 작업트리였다.
이 결과는 소스 회귀·fast-forward 가능성이지 운영 머지, Gstack 전이
런타임, 구독 과금 또는 사용자 설치 준비의 증거가 아니다. 상세 기록은
`E:/Coding Infra/Releases/SimonK-stack/20260928-merge-readiness/report.html`에 있다.

## v21 페르소나 근거와 G5 안전 게이트 격리 후보 (2026-09-28)

`feat/skill-context-budget-260925`의 `5887d8e`에서 v20 이후 추가된
`persona-simulation` 근거 검사와 `/vibe`의 생략 쿼터 확인 G5 차단을
새로운 격리 후보에 포함했다. 이전 v20 후보·사용자 설치본을 덮어쓰지
않았다. 입력 원본 5개는 `distribution/plugin-inputs.v1.json`의 고정 HEAD와
일치하고 clean이었다. Windows CRLF 체크아웃은 원본 설정을 바꾸지 않고
별도 `core.autocrlf=false` 로컬 복제본 5개로 해결했다.

| 산출물 | 전체 영수증 SHA-256 | 범위 |
|---|---|---|
| `source-v21` | `d3056d93e76cc44a9c0c43ad7ebf6c8460c83dc052c9a0935fe595575a3c756c` | 소스 소유 137스킬·411파일 |
| `candidate-safety-v21` | `4e726c41e3c23029923f1bd44b439da18c71d2a7cf5ad5268f25ada052df5486` | 5플러그인·182스킬·736파일 |
| `codex-overlay-v21` | `483d5147184e1838f920f69db033cd03ff5af2b25488202bdbbc654f44cb3d05` | 5개 Codex 호환 manifest를 별도 투영 |

소스 릴리스의 v20 대비 차이는 `vibe`와 `persona-simulation`의
기존 파일 변경 6개·신규 파일 2개다. 후보에는 이 8개와 소스 영수증을
반영한 플러그인 metadata 10개만 바뀌었다. 두 스킬의 핵심 파일 4종은
소스·후보·Codex 오버레이에서 SHA-256이 각각 일치한다. 원본 v20 후보도
기존 digest로 재검증했다. 후보와 오버레이는 시험 후 같은 digest를
다시 통과했다.

오프라인 검증은 후보 `/vibe` 단위 220/220·자체 180/180,
일회용 영수증 검증 복사본의 스모크 4/4, 관련 패키징·페르소나 회귀
119/119, 스킬 validator 두 종 오류·경고 0, Codex manifest 5/5 통과다.
기본 후보 카탈로그는 182개를 찾았다. 정적 경로 감사는 182스킬의
143개 로컬 참조에서 미해결·이식 불가 명령 0개를 찾았지만,
Gstack 직접 참조 31스킬·646회·고유 대상 9개 때문에 종료 1
`external_runtime_pending`이다. 이를 통과로 바꾸거나 전체 런타임
폐쇄로 해석하지 않는다.

새 무인증·네트워크·클립보드 차단 Windows Sandbox에서 Claude Code
2.1.283의 `--init-only` 대조군과 후보 모두 종료 0이었다. 후보는
플러그인 5개·스킬 182개·명령 5개, 디버그 오류 0개를 로드했다.
게스트 네트워크 활성 어댑터는 전후 0, API/OAuth 환경변수는 없었다.
이번에 띄운 Sandbox 세션만 결과 수집 후 종료했다. 재현 스크립트,
WSB 설정 및 원시 로그는
`E:/Coding Infra/Releases/SimonK-stack/20260928-v21-g5-persona/sandbox-init-v21/`에
보존한다. 초기화 성공은 실제 스킬 실행·훅·모델 응답·구독 청구 안전성을
증명하지 않는다.

Codex 오버레이의 5개 manifest는 유효하지만 **오버레이 기본 카탈로그는
여전히 종료 2**다. `zoom-out`의 의도된 Codex 전용 투영 바이트가 기본
원본 후보 영수증과 달라서 `Candidate skill metadata differs from receipt`로
안전하게 차단된다. 명시적 루트·별도 오버레이 검증은 기본 경로의 해결을
대체하지 않는다. 이 구조 선택은 Claude 소유 §35 결정 기록을 기다린다.
PR #54 HTML 규칙, 기존 사용자 프로필 호환, Gstack 전이 런타임,
구독 포함 경로·초과 과금 차단의 실측과 실제 Bot/Orca 연결도 남아 있다.
`runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 모두 `false`다. 사용자 설치·`main` 머지·모델/API/Bot
실호출·결제 설정 변경은 없었다. 전체 증거와 명령은
`E:/Coding Infra/Releases/SimonK-stack/20260928-v21-g5-persona/report.html`에
정리했다.

## v22 PR #54 HTML 규칙 반영 격리 후보 (2026-09-29)

기능 브랜치 `feat/skill-context-budget-260925`의 `977e3cf`에서 PR #54의
`html-default-output`, `simonk-report`, 보고서 템플릿 변경을 새 격리 후보에
반영했다. v21과 사용자 설치본을 덮어쓰지 않았고, 고정된 5개 원본 플러그인
입력의 clean 상태와 HEAD를 재확인했다. 이 단계에는 모델·Bot·Orca 실호출,
결제 설정 변경, 사용자 설치 전환 또는 `main` 머지가 없다.

| 산출물 | 전체 영수증 SHA-256 | 검증 범위 |
|---|---|---|
| `source-v22` | `7c48991e484fedc40a477d0c0a4fddefd48e15c22526d7805c0919a45a0e9471` | 소스 소유 137스킬·411파일 |
| `candidate-safety-v22` | `e0a491f30a0322b1903de9134fe20c13dcc7a0bb4bf6939040c635be5abb174e` | 5플러그인·182스킬·736파일 |
| `codex-overlay-v22` | `f121d43dd0a92406101639a1c6b830b324063c29948501df0c0828970831aa96` | 5개 Codex 호환 오버레이 |

v21 대비 소스 후보 411파일 중 변경은 HTML 규칙 관련 3파일이고, 안전 후보
736파일 중 변경은 그 3파일과 플러그인 영수증을 반영한 metadata 10파일이다.
기존 v21 세 산출물은 각각 원래 digest로 재검증했다. v22의 세 digest도
시험 후 재검증했다.

v22 안전 후보의 기본 `/vibe catalog`는 182개 스킬을 읽었다. 후보 `/vibe`
단위 테스트 220/220, 자체 검사 180/180, 소스 전체 회귀 328건 중
325통과·3건너뜀, 후보 경로를 지정한 프리뷰 회귀 6/6을 확인했다.
건너뛴 3건은 기본 실행에서 후보 경로 환경변수가 없어 생긴 것으로,
별도 6건 실행에 포함되어 통과했다. 정적 경로 감사는 182스킬의
로컬 참조 143건에서 미해결·이식 불가 명령 0건을 찾았지만, Gstack
직접 참조 31스킬·646회·고유 대상 9개가 남아 `external_runtime_pending`
종료 1이다. 이 결과를 전체 런타임 검증으로 해석하지 않는다.

후속 **브라우저 동작 회귀**에서는 v22 후보의 `simonk-report` 템플릿에
모든 절의 테스트 값을 HTML 이스케이프해 채운 별도 fixture를 사용했다.
새 로컬 Chrome 프로필·CDP에서 모바일 요약/상세 탭, 키보드 전환,
드래그→메모, 메모 저장·새로고침 복원, 자동 복사 거부 시 화면 노출,
데스크톱 다크 모드, 인쇄 시 상세 펼침과 PDF 생성을 확인했다.
18/18 검사 통과, 가로 넘침·페이지의 외부 요청·JavaScript 예외는 0건이다.
`scripts/tests/test_simonk_report_browser.py`가 Chrome/Node 가용 환경에서
이를 반복한다. 스크린샷·JSON은 위 v22 폴더의 `interactive-rendered-v2-*`에
보존했다. 이것은 **테스트 데이터로 채운 템플릿**의 브라우저 동작 증거이지
실제 세션 보고 생성, `SendUserFile`, Safari/Firefox 또는 사용자 설치본의
동작 증거는 아니다.
후속 소스 전체 회귀는 329건 중 326통과·3건너뜀·실패 0이며, 건너뛴
후보 경로 시험을 v22 digest로 다시 지정한 별도 프리뷰 6/6도 통과했다.

2026-09-29 **v22 격리 호스트 초기화 실측**: 기존 v21 테스트와 별개의
`sandbox-init-v22/`를 만들고, 네트워크·클립보드가 꺼진 Windows Sandbox에서
고정 SHA-256의 Claude Code 2.1.283과 v22 안전 후보를 읽기 전용으로 매핑했다.
CLI 시작만으로는 게스트 로그온 세션이 생성되지 않아 `LogonCommand`가
실행되지 않았다. 따라서 해당 Sandbox ID를 확인한 뒤
`wsb.exe Execute -r System`으로 동일한 `run.ps1`을 실행했다. 게스트 결과는 control과
후보 `--init-only` 모두 종료 0, 인라인·디렉터리 플러그인 각 5개,
스킬 182개·명령 5개, 디버그 오류 0, 전후 활성 네트워크 어댑터 0개다.
결과는 `sandbox-init-v22/output/result.json`과 디버그 로그에 남겼으며,
실행 후 해당 Sandbox만 종료하고 후보 영수증을 동일 digest로 재검증했다.
이것은 **격리된 Claude 초기화·발견 증거**일 뿐 실제 명령 실행,
사용자 프로필 호환, 모델 응답, 구독 청구 안전성의 증거가 아니다.

2026-09-29 **v22 격리 설치·철회 실측**: 이전 v20 시험의 스크립트를
v22 영수증에 맞춰 고정하고 Claude/Codex에 각각 별도의 새 Windows Sandbox를
사용했다. 두 게스트 모두 네트워크·클립보드가 꺼져 있었고 인증정보 없이
고정 후보와 실행 파일을 읽기 전용으로 매핑했다. 각 게스트의 격리된
`System` 세션에서만 시험 프로필에 다섯 로컬 marketplace와 플러그인을
설치·활성화하고 후보 영수증의 파일별 크기·SHA-256을 검사했다.
Claude Code 2.1.283은 후보 **736/736파일 일치**, 오차 0, 철회 후
설치 플러그인·marketplace 각 0개였다. Claude CLI가 게스트에 남긴
캐시 741파일은 직접 삭제하지 않았고 Sandbox 종료와 함께 격리됐다.
Codex CLI 0.155.0은 오버레이 **742/742파일 일치**, 오차 0, 철회 후
플러그인·marketplace·캐시 모두 0개였다. 전후 활성 네트워크 어댑터는
두 게스트 모두 0개였다. 원시 결과 SHA-256은 Claude
`4c0d1c4641553a22a2568c73892fbbfcaa0eb3548a3b49bb4089cc866769c398`,
Codex `a1bb8aa5620f4b990a8c1ce3ae3f045362c33018864be7489b62afd78c22b438`이며,
각각 `sandbox-install-v22/output/result.json`,
`sandbox-install-codex-v22/output/result.json`에 보존했다. 두 Sandbox는
정확한 ID를 지정해 종료했고, 두 후보 영수증은 동일 digest로 재검증됐다.
이는 **빈 게스트의 설치·바이트 복사·목록 철회** 증거이며 기존 사용자
프로필의 무손실 교체·복구, 스킬 실행, Codex 기본 catalog, 안전 훅,
Gstack 전이 런타임이나 과금 안전성의 증거가 아니다.
시험 후 소스 전체 회귀는 329건 중 326통과·3건너뜀·실패 0이었고,
같은 v22 후보 digest를 지정한 프리뷰 회귀 6/6도 통과했다.

2026-09-29 **v22 합성 기존 프로필 보존·Claude 호스트 갱신 시험**:
호스트 Claude Code의 파일 수정시각이 03:10 KST인 서명 유효한 2.1.284로 바뀌어 기존
2.1.283 SHA-256을 고정한 첫 Sandbox는 후보 설치 전 `EXE_HASH_MISMATCH`로
안전하게 종료됐다. 실패 기록은 `sandbox-profile-claude-v22/output/result.json`에
그대로 보존했다. 새 실행 파일 SHA-256
`0416631e846f743110da5282409776fa1313e65f33a588aae066eaf8db0fda7d`를
고정한 **별도** Sandbox에서는 후보 `--init-only`가 5플러그인·182스킬·
5명령·디버그 오류 0으로 통과했고, 빈 프로필 설치·철회도 736/736파일
일치·오차 0으로 통과했다. 결과는 각각
`sandbox-init-v22-284/output/result.json`(SHA-256
`d1e36c1e2ae7b619e74b6f77ba49ee93785cd7a50e0b5636d3021e6d59424f7d`),
`sandbox-install-claude-v22-284/output/result.json`(SHA-256
`2bf221559f3dfb469f6606d76a97b778ce5597f4c05fb2542876b1f0a8f21fee`)에
남겼다.

또 다른 두 새 Sandbox에는 실제 사용자 프로필이나 인증정보를 복사하지 않고
임의의 기존 플러그인·개인 스킬·설정 마커를 먼저 만든 뒤 v22 다섯 플러그인을
함께 설치·철회했다. Claude 2.1.284와 Codex 0.155.0 모두 시험 중 플러그인
6개를 관측했고, 철회 후 기존 플러그인·marketplace의 목록과 활성 상태,
기존 플러그인 캐시·개인 스킬의 해시, 설정 마커(Claude)가 유지됐다.
Codex의 후보 캐시는 0개,
Claude의 후보 캐시는 게스트 안에 741개 남았다. 결과는
`sandbox-profile-claude-v22-284/output/result.json`(SHA-256
`a5a093a98b1cfcd8387136cadcb1ad2f72c0e294f50e5b27c1485bb25c8a01ce`),
`sandbox-profile-codex-v22/output/result.json`(SHA-256
`60d5ef76c2e0c6bbf30cb92f9f51d556344ae227f9b1ae44e41760fd28e86029`)이다.
통과한 네 게스트의 전후 활성 네트워크 어댑터는 0개였고, 정확한 ID의
Sandbox를 모두 종료했다. 후보·오버레이 영수증도 재검증했다.
이는 **합성 기존 상태와 새 버전의 제한된 보존 시험**이지 실제 사용자
프로필·인증정보·동시 실행·실패 중간 복구의 무손실 이관을 입증하지 않는다.
기본 Codex catalog, Gstack 전이 런타임, 안전 훅, 모델·Bot·Orca 행동과
청구 안전성도 여전히 미검증이다.

Codex 오버레이 자체 영수증 검증과 다섯 명시적 루트 `inventory` 182건은
통과했다. 그러나 오버레이 기본 `catalog`는 여전히
`Candidate skill metadata differs from receipt`로 종료 2다. 이는 의도된
`zoom-out` 투영 바이트와 원본 후보 영수증의 차이이며, 별도 검증과 명시적
루트 우회가 운영용 기본 경로를 해결하지 않는다. 구조 결정과 수정,
Gstack 전이 실행 의존성, 기존 프로필 호환성, 실제 구독 포함 경로의
과금 안전 증거가 남아 있다. `runtime_closure_verified`,
`host_compatibility_verified`, `installation_ready`는 모두 `false`다.
명령·영수증·판정의 상세는
`E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/report.html`에 기록했다.

## v23 Claude Sonnet 5.5 공개 사실 갱신 후보 (2026-09-29)

기능 브랜치 `feat/skill-context-budget-260925`의 `fcab5d2`에서
2026-09-28 출시된 Claude Sonnet 5.5의 공개 사실만 `/vibe` 모델 레지스트리에
반영했다. 공식 [모델 개요](https://platform.claude.com/docs/en/models/overview),
[Sonnet 5.5 모델 문서](https://platform.claude.com/docs/en/models/sonnet-5-5/overview),
[effort 문서](https://platform.claude.com/docs/en/build-with-claude/effort),
[Claude Code 모델 설정](https://code.claude.com/docs/en/model-config)을 확인했다.
API ID `claude-sonnet-5-5`, effort `low`·`medium`·`high`·`xhigh`·`max`,
Claude Code 최소 2.1.284, API 기본 `high`와 CLI 기본 `medium`의 차이를 기록했다.
표준 직접 API 가격은 구독 요금제가 아니므로 계정의 구독 포함 여부를
추론하지 않는다. `sonnet` 별칭도 실제 해석이 관측되기 전에는 실행을 막고,
기존 `claude-sonnet-5`의 전환 상태는 `pending-transport-and-canary`다.

새 격리 폴더는
`E:/Coding Infra/Releases/SimonK-stack/20260929-v23-sonnet55/`이다.
고정된 5개 원본 플러그인 입력의 HEAD와 clean 상태를 확인한 뒤 빌드했으며,
이전 v22 후보·사용자 설치본·`main`은 변경하지 않았다.

| 산출물 | 전체 영수증 SHA-256 | 검증 범위 |
|---|---|---|
| `source-v23` | `c97a16e20c69344b8eef88c42a21b04055fcd9102c23a4f0ec201c7de28320c5` | 소스 소유 137스킬·411파일 |
| `candidate-safety-v23` | `9bcd45c81366619308889b7e8454cc785060185198f986589ffbba4f03063d3d` | 5플러그인·182스킬·736파일 |
| `codex-overlay-v23` | `3a9ff2f8c48f1829ac3b6815a3f8aa45d35515dc70a5559ce7457b90487269af` | Codex 호환 오버레이 |

세 산출물을 각각 `skill_release.py verify`, `plugin_bundle.py verify`,
`codex_overlay.py verify`로 재검증했다. 소스·포장 후보의 모델 레지스트리
검사 각각 28/28, `/vibe` 자체 검사 180/180, 복사 후보의 오프라인
스모크 테스트 4/4가 통과했다. 소스 전체 단위 테스트는 329건 중
326통과·3건너뜀·실패 0이고, 기본 실행에서 후보 경로가 없어 건너뛴
프리뷰 통합 검사는 v23 digest를 지정한 별도 실행에서 6/6 통과했다.
모델·Bot·Orca 실호출, 추가 과금,
결제 설정 변경, 실제 사용자 프로필 설치·전환, `main` 머지는 없었다.
v23 정적 경로 감사는 182스킬·로컬 참조 143건에서 미해결·이식 불가 명령
0건을 찾았지만, Gstack 외부 참조 31스킬·646회·9개 직접 대상 때문에
`external_runtime_pending`(종료 1)이다. v22에서 확인된 Codex 기본
catalog 실패는 v23 오버레이에서도 `Candidate skill metadata differs from
receipt`(종료 2)로 재현됐다. Gstack 전이 런타임 결손도 이 레지스트리
갱신으로 해결되지 않는다. 세 설치 준비 플래그는 계속
`runtime_closure_verified=false`, `host_compatibility_verified=false`,
`installation_ready=false`다. 위 바이트 검증은 모델 접근성·구독 청구 안전성이나
실제 호스트 동작의 증거가 아니다.

2026-09-29 **v23 격리 Claude 초기화 실측**: 별도
`sandbox-init-v23/`의 새 Windows Sandbox에서 네트워크·클립보드 등을
비활성화하고 v23 안전 후보·Claude Code 2.1.284 실행 파일·Git Bash를
읽기 전용으로 연결했다. 게스트에서 인증 환경변수와 자격증명 파일 부재,
실행 파일 SHA-256·후보 영수증을 선확인했다. 무인증 control과 후보
`--init-only`가 모두 종료 0이며 후보에서 인라인·디렉터리 플러그인 각 5개,
스킬 182개, 명령 5개, 디버그 오류 0건, 전후 활성 네트워크 어댑터 0개였다.
`sandbox-init-v23/output/result.json`의 SHA-256은
`ee2e0e65c6c1026b8c5d2f9e759cfb6fd1a46abdcb065110f5a67aba69be0715`다.
게스트 `d46ac383-fbfc-4e9a-a540-91bdc7498432`는
정확한 ID로 종료했고 후보 영수증은 동일 digest로 재확인했다. 이는
격리된 호스트의 **초기화·발견** 증거일 뿐 실제 명령 실행, 기존 사용자
프로필 설치·전환, 모든 런타임 의존성, 모델 접근성 또는 구독 청구
안전성의 증거가 아니다. 세 설치 준비 플래그는 그대로 `false`다.

2026-09-29 **v23 Gstack 전이 효과 재감사(정적)**: 후보의 31개 Gstack 의존
스킬 모두 `gstack-update-check`를 참조한다. 고정된 별도 Gstack 원본
`01593aa67c94780528e8f5121e47362502410ced`의
`bin/gstack-config:153-156`에서 `update_check` 기본값은 `true`이고,
`bin/gstack-update-check:63-66`은 명시적 `false`일 때만 초기에 종료한다.
그 밖의 경로는 `:73-80`에서 오래된 스킬 설명 파일을 삭제할 수 있고,
`:235-250`에서 `git ls-remote` 및 원격 VERSION 조회를 시도한다.
`bin/gstack-egress-lib.sh:93`은 이 업데이트 조회의 영수증 실패 시에도
전송하는 fail-open 분기를 갖는다. 따라서 단순한 직접 helper 존재 확인이나
기본 설정으로 시작하는 Sandbox 성공만으로 무전송·무변경을 주장할 수 없다.

같은 원본에서 `telemetry=off`와 `artifacts_sync_mode=off`는 기본값이지만,
30개 후보 스킬이 참조하는 `gstack-telemetry-log`는 설정에 따라
`gstack-telemetry-sync`로 이어지고, `gstack-learnings-log`·
`gstack-timeline-log`의 백그라운드 `gstack-brain-enqueue`는 동기화 설정 시
큐를 쓴다. `gstack-brain-sync`는 큐를 원격에 push할 수 있다.
30개 스킬이 제시하는 `gstack-team-init`은 **조건부 실행 옵션**이지만
기존 vendored 디렉터리의 `git rm --cached`·`rm -rf`와 프로젝트 지침·훅
변경 경로가 있다. `gstack-config`의 일부 설정/렌더 분기는
`gstack-relink`를 호출해 스킬 링크도 바꾼다. 이 감사는 고정된 별도
원본의 코드 경로를 읽은 것으로 실제 사용자 홈 Gstack을 실행·변경하지
않았고, 모든 동적 분기나 전이 런타임 폐쇄를 입증하지 않는다. 안전한
실행에는 정확한 원본/버전 고정, 전이 파일·플랫폼 도구 검증,
`update_check=false`·`telemetry=off`·`artifacts_sync_mode=off`의
격리된 기본 정책, 전송·팀 초기화의 별도 명시적 게이트에 관한 결정이 필요하다.

2026-09-29 **Sonnet 5.5 Max 대화형 canary**: 후보 바이트를 재검증한 뒤
`scripts/preview-vibe-candidate.ps1`의 정확한 모델 허용 목록에
`claude-sonnet-5-5`를 추가하고, 기존 `claude-sonnet-5` 기본값은 유지했다.
새 빈 임시 작업 폴더에서만 시작하며, 사용자 소스 저장소 신뢰 프롬프트는
거절했고 임시 폴더만 수락했다. 브라우저 연결은 거절했다. 회귀 검사 7/7과
v23의 5플러그인·182스킬 영수증 검사가 통과했다. Claude Code 2.1.284의
시작 화면은 `Sonnet 5.5 with low effort · Claude Max`를 표시했고,
도구를 쓰지 않는 단일 요청에 `VIBE_CANARY_OK`를 반환했다. 세션은 정상 종료,
후보 digest는 종료 후에도 일치했다. API·대체 공급자 인증 환경변수는
비어 있었고 `claude auth status --json`은 `claude.ai`/`firstParty`/`max`였다.
사용자가 usage credits/extra usage 비활성화를 확인했고, 공식
[Claude Code 모델 설정](https://code.claude.com/docs/en/model-config)은 Sonnet 5.5의
네이티브 1M 사용에 별도 usage credits가 필요 없다고 명시한다. 이 경로는
`claude -p`/Agent SDK가 아닌 대화형 세션이다. 따라서 추가 과금 없이
구독 포함 사용량만 소비하도록 제한했지만, CLI는 초과 과금 토글이나 실제
청구 원장을 기계적으로 읽지 못하므로 청구액 실측은 주장하지 않는다.
이 성공은 **Sonnet 5.5의 이 계정 대화형 생성 접근**만 입증한다. 실제
라우팅 선택, 다른 모델/벤더, 기존 사용자 설치본 호환성, Gstack 전이 실행,
Bot/Orca 및 운영 설치는 미검증이다. 이어 같은 조건의 두 번째 대화형
세션에서 `Skill(simonk-core:vibe)`가 실제 호출돼 후보 지침 로드에 성공했다.
모델은 사용할 수 있는 도구가 Skill뿐이라 로컬 파일을 읽거나 스크립트를
실행하지 못했다고 명확히 답했다. 따라서 **명시적 Skill 로딩**만 추가로
검증됐고, `/vibe`의 catalog·plan·dispatch·자동 선택은 여전히 미검증이다.
변경 후 소스 전체 테스트는 330건 중 327통과·3건너뜀·실패 0이며,
후보 경로를 지정한 preview 회귀는 7/7이다. 세 설치 준비 플래그는
여전히 모두 `false`다.

2026-09-29 **v20→v23 Gstack 시작 절차 증거의 바이트 범위 대조**:
v20·v23의 5플러그인 후보 영수증을 각각 원래 digest로 재검증했다.
`gstack/bin/`을 직접 참조하는 `SKILL.md`는 두 후보에서 각각 31개이고,
상대 경로 집합과 31개 SHA-256이 모두 같다(누락·추가·drift 0).
기존 v20 게스트의
`20260928-candidate-gstack-preambles/output-events/results-execute.tsv`에
기록된 31개 스킬 해시를 v23 후보 파일에 다시 대조해 31/31 일치했다.
같은 시험의 `events.json`은 실행된 30개 시작 절차마다 해당 스킬의
`started` 이벤트 1개, 고유 타임라인 해시 30개, 활성 네트워크 어댑터 0을
기록한다. `gstack-upgrade` 1개는 시작 절차가 없어 원래부터 제외됐다.
고정 Gstack 원본도 여전히 clean `01593aa67c94780528e8f5121e47362502410ced`다.
따라서 **v23의 31개 시작 지침 바이트가 기존 v20 동적 시험 입력과 같다**는
범위에서 시험을 재사용할 수 있다. v23 자체의 새 게스트 실행, 스킬 본문
전체, 기본 `update_check=true`의 전송·삭제 경로, 실제 사용자 설치본,
런타임 폐쇄를 증명하지 않는다. 세 설치 준비 플래그는 그대로 `false`다.

2026-09-29 **v23 Gstack 업데이트 기본값의 격리 실행**: 별도 고정 Gstack
원본 `01593aa`의 `bin/`·`lib/`·`VERSION` 195개 파일을 네트워크 차단
Windows Sandbox 게스트에 복사하고 원본과 복사본의 SHA-256을 대조했다.
v23 후보 digest `9bcd45c8...63d3d`, Git Bash·Bun 실행 파일 해시도
시작 전에 확인했다. 활성 네트워크 어댑터 0, API 키 환경변수와 게스트
Codex 인증 파일 부재를 확인했다. 사용자 홈 Gstack은 공유하거나 실행하지
않았다. 동일 게스트의 독립 상태 디렉터리 두 곳에서 오직 테스트용
1,100자 초과 설명 파일을 만들어 `gstack-update-check`를 실행했다.

`update_check: false`인 경우 종료 0, 원격 조회 영수증 0, 캐시·healing
마커 0이고 테스트 파일은 남았다. 설정 파일이 없는 **기본값**은 종료 0,
`github.com`과 `raw.githubusercontent.com`에 대한 조회 **시도**
영수증 2건, 캐시·healing 마커 생성 및 테스트 파일 삭제가 관측됐다.
네트워크가 차단돼 실제 전송은 없었다. 결과는
`E:/Coding Infra/Releases/SimonK-stack/20260929-gstack-update-guard-probe/output/result.json`
(SHA-256 `a95ac180b68f5866fa89e40ffb2911d98a500ad79c03878043f351b15ec43a31`)
이며 스크립트·Sandbox 구성·원시 빈 stdout/stderr도 같은 폴더에 보존했다.
이번 `.wsb` 실행 프로세스는 종료됐다. 별도 CLI 목록에는 이전 시험의
인스턴스 ID가 남아 있어 이번 게스트 ID로 간주하거나 종료하지 않았다.
이 시험은 **업데이트 검사 하나의
두 정책 분기**만 검증한다. 기본값을 안전하다고 승격할 수 없으며,
`update_check=false`만으로 모든 Gstack 실행·텔레메트리·동기화·팀 초기화
경로가 안전하다고 주장하지 않는다. `runtime_closure_verified`,
`host_compatibility_verified`, `installation_ready`는 모두 `false`다.

2026-09-29 **Gstack 학습·동기화·텔레메트리 가드의 호스트 제한 시험**:
새 Sandbox 시작은 기존 `WindowsSandboxClient.exe --help` 프로세스와
단일 인스턴스 충돌(`CO_E_APPSINGLEUSE`)로 결과 파일을 만들지 못했다.
이전 게스트 소유권을 확인할 수 없어 강제 종료하지 않았다. 따라서 아래는
OS·네트워크 격리 시험이 아니라, 별도 호스트 상태 폴더만 지정한 제한 시험이다.

고정 원본 `01593aa`를 Git Bash로 실행하고 사용자 홈 Gstack 대신
`E:/Coding Infra/Releases/SimonK-stack/20260929-gstack-learning-guard-probe/host-state`
만 `GSTACK_HOME`/`GSTACK_STATE_DIR`로 지정했다. 이 폴더의 `config.yaml`에서
`gstack-config get`은 `update_check=false`, `telemetry=off`,
`artifacts_sync_mode=off`를 반환했다. 테스트용 `gstack-learnings-log`는
`projects/guard-probe/learnings.jsonl`에 가짜 기록 1건을 남겼고,
`gstack-learnings-search --query isolated-fixture --limit 1`은 그 기록
1건을 읽었다. `gstack-brain-enqueue`와 `gstack-telemetry-log --no-sweep`은
각각 종료 0이었다. 실행 후 분리 상태 폴더의 파일은 설정과 학습 기록
2개뿐으로, 큐·analytics 파일은 생기지 않았다. 원본 Gstack 작업트리는
clean이며 사용자 프로필 설치본·계정·결제 설정은 수정하지 않았다.

이 결과는 **해당 설정·입력에서 관측된 로컬 파일 효과**만 입증한다.
호스트 네트워크 패킷을 계측하지 않았으므로 무전송·전체 Gstack 런타임
폐쇄·설치 호환성을 주장하지 않는다. `gstack-team-init`, 동기화 활성화,
기본 업데이트 정책은 시험하지 않았고, 세 설치 준비 플래그는 계속 `false`다.

2026-09-29 **구독 경로 재확인과 자동 선택 시험의 도구 경계**:
`runtime_collect.py --surface grok`의 읽기 전용 ACP billing 관측
(06:50:05 KST)은 Grok CLI 주간 사용량 **100%**, 다음 표시상 갱신 시각
2026-10-03 23:12:19 KST, on-demand cap·prepaid balance 각각 0을 반환했다.
`billing.mode=unknown`, `extra_usage_enabled=null`이고 이 수집기는 모델
생성·모델별 구독 포함을 검증하지 않는다. 사용자 설명의 Grok Bot 사용량은
별도 버킷이므로 이 CLI 관측으로 판단하지 않는다. 현재 Grok CLI 생성은
추가 과금 $0 정책상 보류한다. reset 표시도 실제 쿼터 복구 증거가 아니다.

Claude Code는 같은 날 `claude.ai`/`firstParty`/Max 로그인이었고 API·대체
공급자 환경변수 부재, v23 후보 digest와 5플러그인·182스킬을 실행 전
확인했다. 기존 도구 제한 대화형 프리뷰로 자동 Skill 선택을 확인하려 했으나
현재 터미널 도구의 PTY 생성이 두 번 모두 프로세스 시작 전에 실패했다.
표준 입력 파이프 시도는 CLI의 `Input must be provided either through stdin
or as a prompt argument when using --print`로, 프롬프트 없이 종료 1이었다.
자동 선택·스킬 실행의 새 증거는 없고 비대화형 `claude -p`나 API로
우회하지 않았다. 구독 청구 원장도 확인하지 않았으며 준비 플래그는
계속 모두 `false`다.

## v24 원본 플러그인 Windows CI 로캘 수정 후보 (2026-09-29)

기능 브랜치 `feat/skill-context-budget-260925`는 원본 AIHub·Core·Design·Market의
Python 검증 게이트가 Windows 기본 CP949 환경에서 UTF-8 자식 출력을 읽다가
실패하는 문제를 수정한 커밋을 `distribution/plugin-inputs.v1.json`에 고정했다.
각 원본에서 Python 회귀 검사 4/4, 품질 게이트 7/57/19/32가 통과했다.
다섯 원본의 Node 검증은 7/57/19/32/58스킬, Market 9개와 Stack 11개
Node 검사가 통과했다. 이 결과는 각 원본 브랜치의 로컬 검증이며 사용자
설치본의 동작 증거가 아니다.

새 후보는 `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/`에
두었다. 원본 Core 작업트리에는 Git 무시 `.model-cache/`, `.semantic-index/`,
`__pycache__/`가 남아 있어 엄격한 빌더의 실제 파일 인벤토리와 맞지 않았다.
이를 삭제하거나 수정하지 않고, 다섯 고정 커밋을 별도 clean 체크아웃으로
재현해 후보를 빌드했다. 첫 실패의 개별 내부 예외는 빌더가 숨기므로
무시 파일이 그 실패의 단독 원인이라고 단정하지 않는다.

| 산출물 | 전체 영수증 SHA-256 | 범위 |
|---|---|---|
| `source-v24` | `c97a16e20c69344b8eef88c42a21b04055fcd9102c23a4f0ec201c7de28320c5` | 소스 소유 137스킬·411파일 |
| `candidate-safety-v24` | `5f01d6cb732598c305c3c30343bd824d518702ded6323ecc198943d358510a2b` | 5플러그인·182스킬·740파일 |
| `codex-overlay-v24` | `3b1f8d5aa0f3596d504be57d5f793cd78d4f453a9ad147e5f287dc0c373a8990` | Codex 호환 오버레이 |

세 산출물의 개별 `verify`, 5플러그인 입력 회귀 45/45, Claude 후보
check-only 프리뷰가 통과했다. 명시적 다섯 루트 inventory는 182레코드·
문제 0건이었다. 그러나 Codex 오버레이 **기본** catalog는
`Candidate skill metadata differs from receipt`로 종료 1이며, 정적 경로
감사는 미해결 로컬 참조 0건에도 Gstack 외부 런타임 31스킬·646참조·9대상으로
`external_runtime_pending`(종료 1)이다. Inventory는 패키지·행동 평가가
아니며, 새 v24 후보의 호스트 로딩·모델 라우팅·실제 작업은 시험하지 않았다.
`runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 모두 `false`다. 모델·Bot·Orca 실호출, 추가 과금,
사용자 설치·`main` 머지는 없었다. 자세한 영수증과 재현 범위는 위 폴더의
`report.html`에 기록한다.

2026-09-29 **v23→v24 후보 파일 바이트 대조**: 두 safety 후보의 전체
영수증을 원래 digest로 재검증한 뒤 물리 파일별 SHA-256을 비교했다.
v23 737개와 v24 741개(`bundle.json` 포함) 중 추가 4개는 네 원본의
`.github/skill-ci/test_run_ci_encoding.py`다. 기존 파일 변경 13개는
`bundle.json` 1개와 각 원본의 `.github/skill-ci/run_ci.py`,
`.github/workflows/skills-ci.yml`, `README.md` 각 4개뿐이며 삭제는 0개다.
182개 `SKILL.md`와 그 밖의 모든 후보 파일 바이트는 같다.
v24 safety 후보의 **기본** `/vibe catalog`도 종료 0으로 182개 이름을
반환했다. 따라서 이전 v23 격리 호스트 시험의 *스킬·플러그인 실행 입력
바이트*는 v24에서도 유지됐다는 제한된 근거가 있다. 그러나 원본 commit과
영수증은 달라졌고 v24 자체를 새 게스트에서 초기화·설치하지 않았으므로,
v23 호스트 성공을 v24 호스트 검증 완료로 승격하지 않는다. 특히 Codex
**오버레이** 기본 catalog 결함과 Gstack 전이 런타임 게이트는 그대로다.
이 대조 후 소스 `scripts/tests` 전체 단위 검사는 334건 중 331통과·
3건너뜀·실패 0건이었다. 이 검사는 호스트 실행·모델 동작 시험이 아니다.

2026-09-29 **v24 격리 호스트 시험 입력 준비 — 미실행**:
`E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/sandbox-init-v24/`
에 v23의 검증 스크립트와 동일한 v24 전용 입력을 만들었다. 바뀐
스크립트 값은 safety 후보 영수증 digest 하나뿐이며, 실행 파일 SHA-256은
현재 호스트에서 재확인했다. Sandbox 설정의 네트워크·클립보드 비활성,
읽기 전용 입력/후보/실행 파일 매핑과 쓰기 가능한 전용 결과 폴더를
XML로 검사했고 PowerShell 구문 오류 0건이다. `output/result.json`은
존재하지 않는다. 기존 `WindowsSandboxClient.exe --help` PID 100060이
단일 인스턴스를 점유해 새 게스트를 시작하지 않았고, 이 프로세스를
임의 종료하지 않았다. 따라서 v24 실제 초기화·스킬 발견은 **미검증**이다.

2026-09-29 **기존 사용자 평면 스킬 홈과 v24의 SKILL 바이트 차이**:
v24의 정확한 다섯 plugin `skills/`를 소스로 두고, 현재 관측한
Claude `C:/Users/202502/.claude/skills` 및 Codex
`C:/Users/202502/.agents/skills`→`.codex/skills` 순서의 평면 루트를
각각 `orchestrate.py coverage`로 비교했다. 홈 Gstack은 읽기 금지 경계로
명시적 제외했으므로 두 검사의 `scope_complete=false`이며 종료 2다.

| 관측한 평면 루트 | v24와 동일 | 바이트 다름 | 이름 없음 | 범위 밖 고유 이름 |
|---|---:|---:|---:|---:|
| Claude `.claude/skills` | 1 | 137 | 44 | 41 |
| Codex `.agents/skills`→`.codex/skills` | 1 | 136 | 45 | 51 |

양쪽의 정확히 같은 스킬은 `multi-terminal-dispatcher` 하나다. 현재
`~/.claude/skills/vibe`는 2026-09-26 후보를 가리키는 junction이고
버전 2.11.6이며, `.agents/skills/vibe`·`.codex/skills/vibe`도 그 경로로
이어진다. v24 후보 `/vibe`는 2.12.2다. 이 수치는 **선언한 평면 루트의
SKILL.md 바이트**만 비교하며 Claude/Codex의 활성화, 네이티브 플러그인
캐시·프로젝트 로컬 스킬·스크립트/자산 전체, 실제 스킬 선택을 판정하지
않는다. 그러므로 v24가 현재 사용자 프로필에 설치됐거나 호스트 전체에서
누락됐다는 어느 쪽 주장으로도 확대하지 않는다. 기존 링크는 변경하지 않았다.

현재 설치 경로의 `/vibe`가 가리키는
`E:/Coding Infra/Releases/SimonK-stack/20260926-selection-validation/candidate/`
에서 **기본 catalog는** `Candidate skill metadata differs from receipt`
(종료 2)로 실패했다. 그 후보의 `bundle.json` 전체 검증도 실패한다.
영수증의 707파일을 실제 바이트로 대조하면 누락 0, 변경 2
(`vibe/SKILL.md`, `vibe-bot/SKILL.md`), 추가 4
(`model_registry` bytecode 1, `vibe-bot` Relay 참고·감시·검사 자산 3)다.
이 파일들은 기존 사용자/에이전트 변경 가능성이 있으므로 삭제·복구·덮어쓰지
않았다. 이 결과는 현재 **해당 설치 후보의 기본 catalog 사용 불가**를
뜻하지만, 다른 호스트 경로나 명시적 스킬 로드까지 실패했다고 단정하지
않는다. v24 safety 후보의 기본 catalog 통과는 이 설치 경로를 자동 수리하지
않는다.

2026-09-29 **기존 Grok Bot 파일 보존 대조**: 영수증 밖에 있던 현재 설치
후보의 `vibe-bot` Relay 참고·감시·테스트 파일은 v24에도 모두 존재한다.
두 `vibe-bot` 폴더는 각각 10파일이며 old-only/new-only가 0개다.
`bots.json`은 SHA-256이 정확히 같고 19봇·6팀 구성이며,
`bus_watch.py`와 해당 테스트는 줄바꿈만 다르다. 나머지 네 파일의
실질 변경은 `SKILL.md` 0.9.1→0.9.3의 발견 경계, 발동 평가 케이스
추가, Relay 핸드셰이크 목차 추가, Bot 별도 구독 포함 증빙을 요구하는
테스트 fixture 강화다. 기존 파일을 지우지 않고 새 v24에 포장된 Bot
테스트 38/38을 외부 프로세스·네트워크 차단 조건에서 실행했고,
후보 영수증도 다시 통과했다. 이는 파일·오프라인 fixture 보존이지
실제 Grok Bot 계정·Relay 전달·화면 작업의 성공 증거는 아니다.

## v25 Codex 오버레이 기본 catalog 수정 후보 (2026-09-29)

기능 브랜치의 `/vibe` 2.12.3 (`872b4c9`)는 Codex 오버레이가
`zoom-out/SKILL.md`를 수동 호출 전용으로 투영하는 정확한 바이트 변경을
원본 번들·오버레이 영수증 양쪽에 묶어 확인한다. 기존 기본 catalog는
원본 해시만 읽어 정상 오버레이도 거부했다. 새 검사는 변조 파일뿐 아니라
투영 파일과 영수증을 함께 재작성한 경우도 거부하도록 회귀 검사를 포함한다.
기존 v24 후보와 설치본은 변경하지 않았다.

새 후보는 `E:/Coding Infra/Releases/SimonK-stack/20260929-v25-overlay-catalog/`에
보존한다. 다섯 원본 플러그인 입력 커밋은 v24와 같고, 소스 소유 `/vibe`
변경만 반영했다.

| 산출물 | 전체 영수증 SHA-256 | 결과 |
|---|---|---|
| `source-v25` | `72c43589dd569c7c5c81ad133fc6c1c0d0fb2929d66031e23ec6b6fb2dbd4238` | 137스킬·411파일, verify 0 |
| `candidate-safety-v25` | `d30d0f7e2853a6a0caf39e46c30baaeea42b6014c02718613a2a7df04a9ec434` | 5플러그인·182스킬·740파일, verify 0 |
| `codex-overlay-v25` | `cd3691dfa149bdde943d9fa7ab0909f2057bf4d3a088caa7d9187a8c8f57b6a8` | Codex 호환 오버레이, verify 0 |

안전 후보와 Codex 오버레이의 **기본** `/vibe catalog`가 각각 종료 0,
182개 이름을 반환했다. 포장된 `/vibe` 단위 검사 222/222, 소스 전체
단위 검사 334건 중 331통과·3건너뜀·실패 0, 스킬 validator 오류·경고
0이었다. Claude 후보의 다섯 플러그인 check-only 프리뷰도 모델 호출 없이
통과했다. 정적 경로 감사에서는 로컬 누락·이식 불가 명령 0건이지만
Gstack 외부 런타임 31스킬·646참조·9대상으로
`external_runtime_pending`(종료 1)이 유지된다. Windows Sandbox의
v25 초기화·실제 호스트 선택·모델 라우팅·Bot/Orca 실행은 시험하지
않았다. `runtime_closure_verified`, `host_compatibility_verified`,
`installation_ready`는 계속 `false`다. 추가 과금·모델 실호출·사용자 설치·
`main` 머지는 없었다. 자세한 범위와 재현 결과는 같은 폴더의
`report.html`을 본다.

## v25 Codex 일반 subset 격리 설치·철회 검증 (2026-09-29)

v25 Codex 오버레이 digest `cd3691dfa149bdde943d9fa7ab0909f2057bf4d3a088caa7d9187a8c8f57b6a8`에서
별도 `codex-general-subset-v25`를 생성했다. subset digest는
`4cfdce3dada51af3e5351aca271e9b98df5913cf076a6d260d6e8694d03b78c6`이며,
원본 오버레이를 함께 넣은 검증이 생성 직후와 격리 호스트 시험 뒤 모두
`source_provenance_verified=true`·종료 0이었다. D-29의 다섯 스킬
(`careful`, `freeze`, `guard`, `investigate`, `unfreeze`)과 Core/Stack 안전
런타임은 제외되고, 명시적 다섯 `--root` 인벤토리는 177개·문제 0건,
`vibe` 1개·제외 스킬 0개다. 원본 `bundle.json`이 182개 출처를 보존하므로
이 subset의 기본 번들 catalog 성공을 주장하지 않는다.

새 무인증 `CODEX_HOME`을
`E:/Coding Infra/Releases/SimonK-stack/20260929-v25-overlay-catalog/codex-hostprobe-v25/`
에만 만들고, Codex CLI 0.155.0으로 로컬 마켓플레이스 다섯 개와 플러그인
다섯 개를 등록했다. 캐시 723파일은 subset의 동일 상대 경로·SHA-256과
모두 일치했고, 실제 캐시 `SKILL.md`는 177개, 제외 대상 파일 0개였다.
이후 정확한 테스트 프로필에서만 다섯 플러그인과 마켓플레이스를 철회해
설치 목록·가용 목록·마켓플레이스·캐시 파일이 각각 0개임을 확인했다.
삭제된 것은 생성한 테스트 캐시 복사본뿐이며 원본 subset은 보존했다.
기존 사용자 Codex 프로필은 SimonK 플러그인 0개(전체 20개), flat
`vibe`는 여전히 2.11.6이었다. 테스트 프로필에는 인증 파일이 없고
`config.toml`만 남았다.

이는 **복사 바이트·등록·철회**의 격리 검증이다. 실제 177개 스킬 선택,
Codex 정책 훅 집행, Gstack 런타임 폐쇄, 사용자 홈 무손실 전환, 모델/Bot/
Orca 사용은 입증하지 않는다. 모델 호출과 추가 과금은 없었다.
`host_compatibility_verified`와 `installation_ready`는 계속 `false`이며,
설치 전환·`main` 머지는 하지 않았다. 상세는 같은 릴리스 폴더의
`report-subset.html`에 둔다.

2026-09-29 **v25 Claude 격리 호스트 입력 준비 — 미실행**:
`E:/Coding Infra/Releases/SimonK-stack/20260929-v25-overlay-catalog/sandbox-init-v25/`
에 v24에서 검증한 `run.ps1`·`sandbox.wsb`를 별도로 복제하고, 안전 후보
`bundle.json`의 실제 SHA-256
`d30d0f7e2853a6a0caf39e46c30baaeea42b6014c02718613a2a7df04a9ec434`
및 v25 전용 읽기 전용 매핑 경로로 갱신했다. PowerShell 파서 오류 0,
Sandbox 네트워크·클립보드 비활성, 매핑 5개 중 4개 읽기 전용·1개 전용
출력 폴더, 누락 매핑 0개를 확인했다. 결과 `output/result.json`은 없다.
기존 `WindowsSandboxClient.exe` 창이 실행 중이어서 그 세션을 종료하거나
새 게스트를 시작하지 않았다. 따라서 Claude 후보의 실제 초기화·발견은
**미검증**이고 설치 준비 플래그는 여전히 `false`다. 별도로
`runtime_collect`·`orchestrate` 오프라인 테스트 120/120을 통과했지만
이는 구독 계정의 모델별 포함 여부·쿼터·실호출·청구 안전성을 증명하지 않는다.
모델/API/Bot/Orca 호출, 결제 설정 변경, 사용자 설치·`main` 머지는 없었다.

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
