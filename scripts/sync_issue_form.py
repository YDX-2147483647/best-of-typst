"""Sync categories and labels to the issue template form

projects.yaml → .github/ISSUE_TEMPLATE/01_suggest-project.yml

Note that this script does NOT update `.vscode/projects.schema.json`.
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Literal


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description=__doc__,
        epilog="Read from source, substitute the content in destination between "
        "“# sync-{categories,labels}: start” and “# sync-{categories,labels}: end”.",
    )
    parser.add_argument("source", type=Path, help="projects.yaml")
    parser.add_argument(
        "destination", type=Path, help=".github/ISSUE_TEMPLATE/01_suggest-project.yml"
    )
    return parser


def format_categories(projects_yaml: dict, *, tab: str) -> Generator[str, None, None]:
    return (f"{tab}- {c['title']}" for c in projects_yaml["categories"])


def format_labels(projects_yaml: dict, *, tab: str) -> Generator[str, None, None]:
    return (
        f"""{tab}- label: {label["name"]} — {label["description"]}""".strip("\n")
        for label in projects_yaml["labels"]
    )


def transform(issue_template: str, projects_yaml: dict) -> str:
    original_rows = issue_template.splitlines()

    rows: deque[str] = deque()
    interlude: None | Literal["categories", "labels"] = None
    for r in original_rows:
        match (interlude, r.strip()):
            case (None, "# sync-categories: start"):
                rows.append(r)

                tab = r[: r.index("#")]
                rows.extend(format_categories(projects_yaml, tab=tab))
                interlude = "categories"
            case (_, "# sync-categories: end"):
                rows.append(r)
                interlude = None

            case (None, "# sync-labels: start"):
                rows.append(r)

                tab = r[: r.index("#")]
                rows.extend(format_labels(projects_yaml, tab=tab))
                interlude = "labels"
            case (_, "# sync-labels: end"):
                rows.append(r)
                interlude = None

            case (None, _):
                rows.append(r)

            case _:
                # Skip original interludes
                pass

    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    args = build_parser().parse_args()
    src: Path = args.source
    dst: Path = args.destination

    yaml = YAML(typ="safe")
    projects_yaml = yaml.load(src.read_text(encoding="utf-8"))
    issue_template = dst.read_text(encoding="utf-8")

    dst.write_text(transform(issue_template, projects_yaml), encoding="utf-8")
