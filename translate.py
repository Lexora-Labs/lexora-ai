"""Legacy translation script kept only for backward compatibility.

Use the canonical CLI entrypoint instead:
    lexora translate <input> <output> --target <lang> [options]
"""

import sys


def main() -> None:
    """Fail fast and redirect users to the canonical CLI pipeline."""
    print(
        "translate.py is deprecated.\n"
        "Use 'lexora translate <input> <output> --target <lang>' instead.",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()