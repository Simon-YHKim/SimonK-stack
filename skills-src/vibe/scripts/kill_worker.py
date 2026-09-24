"""Retired legacy worker killer; no process discovery or termination capability.

Environment handles never proved dispatch/process ownership. Keep this inert
entrypoint so old callers fail explicitly instead of finding a mutable home
installation or treating an incomplete scan as successful cleanup. A future
guarded native stop adapter needs separate authorization and runtime evidence.
"""
import argparse
import json
import sys


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--help"], ["-h"]):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--dispatch", help="Retired target option; never executed")
        parser.add_argument("--handle", help="Retired environment-handle option; never scanned")
        parser.add_argument("--kill", action="store_true", help="Retired; always rejected")
        parser.add_argument("--fence", action="store_true", help="Retired; always rejected")
        parser.print_help()
        return 0
    # Do not parse/echo target values, import native/process helpers, or expose
    # force/environment overrides. Even the former 'dry' path was not evidence
    # of ownership or absence and must not be reported as successful cleanup.
    print(json.dumps({"ok": False, "error": "LEGACY_WORKER_TERMINATION_DISABLED",
        "status": "retired", "termination_verified": False,
        "next": "Keep G8 blocked until a separately authorized, owned native stop path is verified."}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
