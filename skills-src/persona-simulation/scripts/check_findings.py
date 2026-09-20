"""페르소나 시뮬 리포트 자가 점검 — 막는 쪽이 기본이다(fail-closed).

왜 bash 가 아니라 여기인가 (2026-09-20 보안 게이트 지적):
  - 파일이 둘 이상이면 grep 이 줄 앞에 **파일명을 붙인다**. 그래서 `persona-sim-x.tsx:7.html`
    같은 이름만으로 "근거 있음" 필터를 통과시킬 수 있었다(GA-01).
  - 읽기 실패한 파일이 있어도 뒤의 `wc` 가 상태를 덮어 부분 집합만으로 OK 가 났다(GA-02).
  - HTML 이 한 줄이면 줄 단위 grep 은 발견과 근거를 붙여놓고도 구분하지 못한다(B5).
  - 근거 있는 발견이 0건인 **정당한 실행**이 통과할 길이 없었다(B3).
  - 지난 실행의 리포트가 이번 실행의 부재를 가릴 수 있었다(B4).

판정
  0  통과   — 근거 있는 발견이 1건 이상이거나, 0건인데 범위 선언이 있다
  1  불합격 — 리포트 없음 / 읽기 실패 / 근거 없는 발견 / 0건인데 범위 선언 없음

쓰는 법
  python scripts/check_findings.py                      # 현재 폴더의 persona-sim-*.html
  python scripts/check_findings.py --expect persona-sim-2026-09-20.html
  python scripts/check_findings.py a.html b.html
"""
import argparse
import glob
import os
import re
import sys

KIND = re.compile(r"(BLOCKER|DROPOUT|DISTRUST|CONFUSION)")
# 근거 = 코드 위치 표기. 발견 표식 뒤 이 창 안에 있어야 그 발견의 근거로 인정한다.
EVIDENCE = re.compile(r"[\w./-]+\.(?:tsx|ts|jsx|js|py|kt|swift):\d+")
WINDOW = 400
# 발견이 0건일 때 "정말 0건"을 선언하는 표식. 무엇을 어디까지 걸었는지 함께 적어야 한다.
SCOPE = re.compile(r"PERSONA-SCOPE:\s*\S+")


def read(path):
    """(본문, 오류). 디렉터리·읽기 실패는 오류로 돌려준다 - 조용히 건너뛰지 않는다."""
    if os.path.isdir(path):
        return None, "디렉터리다"
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(), None
    except OSError as e:
        return None, f"{type(e).__name__}: {e.strerror or e}"


def check_text(text):
    """(발견 수, 근거 없는 발견 목록). 파일명은 보지 않는다 - 본문만 본다."""
    total, bad = 0, []
    for m in KIND.finditer(text):
        total += 1
        window = text[m.end():m.end() + WINDOW]
        if not EVIDENCE.search(window):
            around = re.sub(r"\s+", " ", text[m.start():m.start() + 90]).strip()
            bad.append(around)
    return total, bad


def main(argv=None):
    # Windows 기본 콘솔은 cp949 라 em dash 하나로 UnicodeEncodeError 가 난다. 검사기가
    # 판정 대신 트레이스백을 뱉으면 그것도 fail-open 의 한 종류다(2026-09-20 자체 실행에서 터졌다).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="*", help="검사할 리포트. 비우면 persona-sim-*.html")
    ap.add_argument("--expect", default="",
                    help="이번 실행이 만들었어야 하는 리포트. 없으면 불합격")
    a = ap.parse_args(argv)

    reports = a.reports or sorted(glob.glob("persona-sim-*.html"))
    if a.expect and a.expect not in reports and os.path.exists(a.expect):
        reports.append(a.expect)

    if a.expect and not os.path.exists(a.expect):
        print(f"불합격: 이번 실행의 리포트가 없다 - {a.expect}")
        print("  (다른 리포트가 있어도 이번 실행의 부재를 대신하지 못한다)")
        return 1
    if not reports:
        print("불합격: 리포트가 없다 - 점검할 대상 자체가 없다. 실행이 끝나지 않은 것이다.")
        return 1

    total, bad, errors, scoped = 0, [], [], False
    for path in reports:
        text, err = read(path)
        if err:
            errors.append(f"{path}: {err}")
            continue
        if SCOPE.search(text):
            scoped = True
        n, b = check_text(text)
        total += n
        bad.extend(f"{path}: {line}" for line in b)

    if errors:
        print(f"불합격: 읽지 못한 리포트 {len(errors)}건 - 검사하지 못한 파일이 있으면 통과가 아니다")
        for e in errors[:10]:
            print("  " + e)
        return 1
    if bad:
        print(f"불합격: 근거(file:line) 없는 발견 {len(bad)}건")
        for line in bad[:20]:
            print("  " + line)
        return 1
    if total == 0:
        if scoped:
            print("통과: 발견 0건이고 범위 선언(PERSONA-SCOPE)이 있다")
            return 0
        print("불합격: 발견이 0건인데 범위 선언이 없다")
        print("  정말 0건이면 리포트에 'PERSONA-SCOPE: <어느 화면을 어느 페르소나로 걸었는지>' 를 적어라")
        return 1
    print(f"통과: 발견 {total}건 전부에 코드 근거 있음 (리포트 {len(reports)}개)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
