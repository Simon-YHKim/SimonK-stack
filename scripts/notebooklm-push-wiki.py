"""
notebooklm-push-wiki.py — SimonKWiki 핵심 wiki 페이지 → NotebookLM workspace 자동 push

사용:
    python scripts/notebooklm-push-wiki.py [--workspace <id>] [--category <concepts|projects|...>] [--dry-run]

전제:
    notebooklm CLI 로그인 완료 (notebooklm doctor → Auth: pass)
    notebooklm-py v0.4.1+ 설치 (uv tool install notebooklm-py)

동작:
    1. wiki/<category>/*.md 파일 list
    2. 각 파일 → notebooklm source add <file>
    3. 결과 log + dry-run 모드 지원

기본 target workspace: SimonKWiki (7d9750db)
"""
import argparse
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

WIKI = r"E:\Coding Infra\obsidian\SimonKWiki\wiki"
DEFAULT_WORKSPACE = "7d9750db"  # SimonKWiki

# 핵심 카테고리 우선순위 (Phase 별)
CORE_CATEGORIES = {
    "concepts": "★ 9 회로 + Brain Trinity + AI 면접 논문 + design 워크플로우",
    "entities/tools": "★ 도구 stack + MCP 통합",
    "entities/people": "관계 영역 (소하·brother·parents)",
    "events": "결정적 사건 catalog",
    "arcs": "어두운 8 + 밝은 7 호",
    "projects": "★ 진행 중 (ai-pivot · current-pivot · android-app-launch · simonk-stack)",
    "protocols": "★ Operations v1 + Blueprint v1.0 + MCP integration",
    "assessments": "Birkman + MBTI + 자기인식 도구 로드맵",
}

def find_md_files(category):
    """카테고리 안 .md 파일 list"""
    cat_dir = os.path.join(WIKI, category)
    if not os.path.isdir(cat_dir):
        return []
    files = []
    for root, _, fnames in os.walk(cat_dir):
        for fn in fnames:
            if fn.endswith('.md'):
                files.append(os.path.join(root, fn))
    return sorted(files)

def push_to_notebooklm(workspace, file_path, dry_run=False):
    """notebooklm source add <file> 호출"""
    if dry_run:
        print(f"  [DRY-RUN] notebooklm source add '{file_path}'")
        return True
    try:
        result = subprocess.run(
            ['notebooklm', 'source', 'add', file_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60
        )
        if result.returncode == 0:
            return True
        else:
            print(f"  ERROR: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default=DEFAULT_WORKSPACE,
                        help=f'NotebookLM workspace ID prefix (default: {DEFAULT_WORKSPACE} SimonKWiki)')
    parser.add_argument('--category', choices=list(CORE_CATEGORIES.keys()) + ['all'], default='all',
                        help='카테고리 선택 (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='실제 push X, 명령만 출력')
    args = parser.parse_args()

    # 1. workspace 활성화
    print(f"# NotebookLM Push — workspace: {args.workspace}\n")
    if not args.dry_run:
        result = subprocess.run(['notebooklm', 'use', args.workspace],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            print(f"FATAL: workspace activate fail — {result.stderr}")
            sys.exit(1)
        print(f"  Workspace activated\n")

    # 2. 카테고리 결정
    categories = [args.category] if args.category != 'all' else CORE_CATEGORIES.keys()

    total_ok = 0
    total_fail = 0
    for cat in categories:
        files = find_md_files(cat)
        print(f"## {cat} ({len(files)} files)\n")
        print(f"  {CORE_CATEGORIES.get(cat, '')}\n")
        for fp in files:
            ok = push_to_notebooklm(args.workspace, fp, args.dry_run)
            if ok:
                total_ok += 1
                print(f"  + {os.path.basename(fp)}")
            else:
                total_fail += 1
        print()

    print(f"\n=== DONE: {total_ok} added, {total_fail} fail ===")
    print(f"\n다음 사용:")
    print(f"  notebooklm use {args.workspace}")
    print(f"  notebooklm ask \"<통합 질의>\"")
    print(f"  notebooklm generate quiz  # 면접 준비")

if __name__ == "__main__":
    main()
