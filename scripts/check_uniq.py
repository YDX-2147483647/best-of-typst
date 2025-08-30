"""Check the uniqueness of projects in projects.yaml

- `name`s must be unique.
- Repo IDs should be unique, except monorepos.
- Other IDs must be unique.

Special cases are declared in the `EXPECT` variable below.

Prerequisite: [yq](https://mikefarah.gitbook.io/yq).
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter, deque
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from subprocess import run

from ruamel.yaml import YAML

EXPECT: list[tuple[str, str, int]] = [
    # tinymist and typlite
    ("github_id", "Myriad-Dreamin/tinymist", 2),
    # the crate and wasi-stub
    ("github_id", "astrale-sharp/wasm-minimal-protocol", 2),
]


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("projects_yaml", type=Path, help="projects.yaml")
    return parser


def check_uniq(projects_yaml: Path) -> None:
    # Collect `*_id` keys
    yaml = YAML(typ="safe")
    content = yaml.load(projects_yaml)
    keys: set[str] = set(chain(*(p.keys() for p in content["projects"])))
    id_keys = {k for k in keys if k.endswith("_id") or k == "name"}

    validate(EXPECT, id_keys=id_keys)

    repeated = False
    for key in id_keys:
        repeated |= check_key_repeated(key, projects_yaml)

    if repeated:
        exit(1)


def validate(expect, *, id_keys: set[str]) -> None:
    for k, _v, n in expect:
        assert k in id_keys
        assert n > 1


def check_key_repeated(key: str, projects_yaml: Path) -> bool:
    """If repeated, return true and print report; otherwise, return false."""
    lines = run(
        [
            "yq",
            f'.projects.[] | select(has("{key}")) | line + " " + .{key}',
            projects_yaml,
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()

    # Parse into (line number, value)
    records = list(map(parse_yq_stdout, lines))

    # Find repeated values
    count = Counter(r.value for r in records)

    expected_count = {v: n for k, v, n in EXPECT if k == key}
    warnings: deque[str] = deque()
    for v, n in expected_count.items():
        if count[v] != n:
            warnings.append(
                f"Expect that `{v}` would occur {n} times, but it actually occurs {count[v]} time(s)."
            )

    repeated_values: deque[str] = deque()
    for v, n in count.items():
        if (expected := expected_count.get(v)) is not None:
            if n != expected:
                repeated_values.append(v)
        elif n > 1:
            repeated_values.append(v)

    if repeated_values or warnings:
        print(f"## `{key}`", end="\n\n")
        if repeated_values:
            print("Found repeated values:", end="\n\n")
            print("```")
            for r in records:
                if r.value in repeated_values:
                    print(f"{r.line_number: >3}  {r.value}")
            print("```", end="\n\n")

        if warnings:
            print("Warnings:", end="\n\n")
            for w in warnings:
                print(f"- {w}")
            print("")

    return bool(repeated_values)


@dataclass
class Record:
    line_number: str
    value: str


def parse_yq_stdout(line: str) -> Record:
    parts = line.strip().split(" ", maxsplit=1)
    assert len(parts) == 2, f"failed to parse into Record(line_number, value): {line}"
    return Record(line_number=parts[0], value=parts[1])


if __name__ == "__main__":
    args = build_parser().parse_args()
    projects_yaml: Path = args.projects_yaml
    check_uniq(projects_yaml)
