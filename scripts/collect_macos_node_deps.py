from __future__ import annotations

import pathlib
import subprocess
import sys


def is_system_library(path: str) -> bool:
    return path.startswith('/usr/lib/') or path.startswith('/System/Library/')


def main() -> int:
    if len(sys.argv) != 3:
        print('usage: collect_macos_node_deps.py <source_bin> <output_file>', file=sys.stderr)
        return 2

    source = pathlib.Path(sys.argv[1]).resolve()
    output = pathlib.Path(sys.argv[2])
    visited: set[pathlib.Path] = set()
    discovered: set[pathlib.Path] = set()
    results: list[pathlib.Path] = []
    stack = [source]

    while stack:
        current = stack.pop()
        if current in visited or not current.exists():
            continue
        visited.add(current)

        proc = subprocess.run(
            ['otool', '-L', str(current)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            continue

        for raw_line in proc.stdout.splitlines()[1:]:
            line = raw_line.strip()
            if not line:
                continue
            dep_text = line.split(' (compatibility version', 1)[0].strip()
            if not dep_text.startswith('/'):
                continue
            if is_system_library(dep_text):
                continue

            dep = pathlib.Path(dep_text)
            if not dep.exists() or dep in visited or dep in discovered:
                continue

            discovered.add(dep)
            results.append(dep)
            stack.append(dep)

    output.write_text('\n'.join(str(path) for path in results) + ('\n' if results else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
