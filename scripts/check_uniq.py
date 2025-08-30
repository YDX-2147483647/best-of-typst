"""Check the uniqueness of projects in projects.yaml

- `name`s must be unique.
- Repo IDs should be unique, except monorepos.
- Other IDs must be unique.

Prerequisite: [yq](https://mikefarah.gitbook.io/yq).
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from subprocess import run

from ruamel.yaml import YAML


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

    repeated = False
    for key in id_keys:
        repeated |= check_key_repeated(key, projects_yaml)

    if repeated:
        exit(1)


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
    repeated_values = [v for (v, n) in count.items() if n > 1]

    if repeated_values:
        print(f"## Found repeated `{key}`s", end="\n\n")
        print("```")
        for r in records:
            if r.value in repeated_values:
                print(f"{r.line_number: >3}  {r.value}")
        print("```", end="\n\n")

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
