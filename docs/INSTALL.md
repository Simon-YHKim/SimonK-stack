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
해석합니다. 종료 1은 `unresolved`에 대한 **문맥 검토 필요**이지 파일 누락
확정이나 실행 실패 증명이 아닙니다. 동적 경로·절대 호스트 경로·import·서비스·
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

읽기 전용 라우팅 세션은 위 명령에 `-Run -SubscriptionOnlyConfirmed`를
**명시적으로** 더할 때만 시작된다. 정확한 Max 구독 로그인과 API/대체
제공자 환경변수 부재를 재검사하며, 그 자식 프로세스에만
`ENABLE_CLAUDEAI_MCP_SERVERS=false`를 설정하고 `--strict-mcp-config`,
Core-inline 한 개, Sonnet 5 `low`, plan mode, `Skill` 도구만 사용한다.
환경변수 차단과 초과 사용 설정의 실제 효과·호스트 컨텍스트 절감은
아직 모델을 재호출해 실측하지 않았다. 실행기는 사용자에게 설정 확인을
요구하지만 초과 사용 비활성화를 기계적으로 증명하지 못한다. 일반 작업
실행이나 설치가 아닌 라우팅 미리보기이며 GUI/봇/Orca 조작은 불가하다.
새 테스트는 RED 3건을 재현한 뒤 GREEN 3건 및 실제 v15 후보
`CheckOnly` 1건 및 가짜 API 키 차단 1건을 통과했다. 가짜 키가 있을 때 `-Run`은 모델 시작 전
`NON_SUBSCRIPTION_CREDENTIAL_PRESENT`로 차단됐다.

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
