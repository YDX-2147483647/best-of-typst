"""Add a project from an issue

python add_project.py --help
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from typing import Callable, TypeAlias


if TYPE_CHECKING:
    Transformer: TypeAlias = Callable[[str], dict[str, str]]
    """original_value ⇒ { key: value }
    
    `value` will appear in YAML, unescaped. For example, `{ "key": "123"}` will turn into `key: 123`, where the value is a number.
    """


def url_to_id(url: str) -> dict[str, str]:
    u = urlparse(url.strip())
    match u.netloc:
        case "github.com" | "gitee.com" | "gitlab.com":
            key = f"{u.netloc.removesuffix('.com')}_id"
            return {key: u.path.removeprefix("/").removesuffix("/")}
        case "greasyfork.org":
            m = re.match(R"^/scripts/(?P<id>\d+)-", u.path)
            assert m is not None, f"Fail to parse Greasy Fork URL path: {u.path}"
            return {"greasy_fork_id": m.group("id")}
        case _:
            raise Exception(f"Cannot recognize URL netloc “{u.netloc}”: {url}")


def parse_labels(
    labels_section: str, labels_config: list[dict[str, str]]
) -> dict[str, str]:
    """Parse selected labels from checkboxes"""
    # Create mapping from display name to internal label
    label_mapping = {label["name"]: label["label"] for label in labels_config}

    selected_labels: list[str] = []

    for line in labels_section.strip().splitlines():
        if line.startswith("- [x]"):
            # Extract the label name (emoji + text before the first '—')
            match = re.match(r"- \[x\] (.+?) —", line)
            if match:
                label = match.group(1).strip()
                assert label in label_mapping, f"unknown label: {label}"
                selected_labels.append(label_mapping[label])

    if selected_labels:
        return {"labels": f"[{', '.join(selected_labels)}]"}
    return {}


def parse_package_registries(registries_text: str) -> dict[str, str]:
    """Parse package registry URLs and extract IDs"""
    result = {}

    for line in registries_text.strip().splitlines():
        url = line.strip()
        if not url:
            continue

        parsed = urlparse(url)
        path = parsed.path
        match parsed.netloc:
            case "pypi.org":
                # Example: https://pypi.org/project/showman/
                result["pypi_id"] = path.removeprefix("/project/").removesuffix("/")
            case "www.npmjs.com":
                # Example: https://www.npmjs.com/package/astro-typst
                result["npm_id"] = path.removeprefix("/package/")
            case "crates.io" | "lib.rs":
                # Example: https://crates.io/crates/typstyle or https://lib.rs/crates/tinymist
                result["cargo_id"] = path.removeprefix("/crates/")
            case "pkg.go.dev":
                # Example: https://pkg.go.dev/github.com/francescoalemanno/gotypst
                result["go_id"] = path.removeprefix("/")
            case "central.sonatype.com" | "search.maven.org":
                # Example: https://search.maven.org/artifact/io.github.fatihcatalkaya/java-typst
                result["maven_id"] = path.removeprefix("/artifact/").replace("/", ":")
            case other:
                assert False, f"{other} is not supported yet: {url}"

    return result


def build_transformers(project_yaml: str) -> dict[str, Transformer]:
    """
    @param project_yaml: content of `project.yaml`
    @return transformers: { original_key: original_value ⇒ { key: value} }
    """
    yaml = YAML(typ="safe")
    project_config = yaml.load(project_yaml)

    categories = project_config["categories"]
    labels = project_config["labels"]

    return {
        "Name": lambda v: {"name": v.strip()},
        "URL": url_to_id,
        "Category": lambda v: {
            "category": next(
                c["category"] for c in categories if c["title"] == v.strip()
            )
        },
        "Labels": lambda v: parse_labels(v, labels),
        "Package registries": parse_package_registries,
    }


def parse_issue_body(body: str, transformers: dict[str, Transformer]) -> dict[str, str]:
    # Ignore additional context
    body = body[: body.index("### Additional context")]

    # Split into sections
    sections = body.removeprefix("### ").replace("\r\n", "\n").split("\n\n### ")
    pairs = (s.split("\n\n", maxsplit=1) for s in sections)

    # Transform
    project = {}
    for k, v in pairs:
        if v.strip() != "_No response_":
            project |= transformers[k](v)
    return project


def dump(project: dict[str, str], project_yaml: str) -> str:
    last_line = project_yaml.splitlines()[-1]
    tab = re.match(R"^(\s*)  ", last_line).group(1)  # type: ignore
    return f"{tab}- " + f"\n{tab}  ".join(f"{k}: {v}" for k, v in project.items())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append a project from stdin to project.yaml",
        epilog=f"""This script does not request GitHub API. Use it with GitHub CLI.

    gh issue view … --json body | python {__file__} ./project.yaml""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_yaml", type=Path, help="Path to project.yaml")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    project_yaml_path: Path = args.project_yaml
    project_yaml = project_yaml_path.read_text(encoding="utf-8")

    project = parse_issue_body(
        body=json.loads(input())["body"],
        transformers=build_transformers(project_yaml),
    )

    patch = dump(project, project_yaml)
    print(patch)
    with project_yaml_path.open("a", encoding="utf-8") as f:
        f.write(f"\n{patch}\n")
