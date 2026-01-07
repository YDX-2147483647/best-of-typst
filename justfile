set dotenv-load
python := env_var_or_default('PYTHON','python')

# List available recipes
@default:
    just --list

# Install or upgrade dependencies
bootstrap:
    {{ python }} -m pip install --upgrade ruamel.yaml

# Sync categories and labels to the issue template form
sync-issue-form *ARGS:
    {{ python }} ./scripts/sync_issue_form.py ./projects.yaml ./.github/ISSUE_TEMPLATE/01_suggest-project.yml {{ ARGS }}

# List suggestions of adding projects
list-project-suggestions:
    gh issue list --label add-project

# Add a project from issue
add-project ISSUE_NUMBER:
    gh issue view {{ ISSUE_NUMBER }} --json body | {{ python }} ./scripts/add_project.py ./projects.yaml

# Check the uniqueness of projects
check-uniq *ARGS:
    {{ python }} ./scripts/check_uniq.py ./projects.yaml {{ ARGS }}

# Package the typst generator as a publishable template package
[arg('version', pattern='\d+\.\d+\.\d+')]
package version:
    -rm -r package/
    mkdir -p package/example/
    cp scripts/history_to_json.py package/example/
    cp -r typ package/
    mv package/typ/main.typ package/example/
    mv package/typ/{typst.toml,README.md,LICENSE,thumbnail.webp} package/

    sd '^# NOTE: .+$' '' package/typst.toml
    sd --fixed-strings 'version = "0.0.0"' \
        {{ quote('version = "' + version + '"') }} \
        package/typst.toml

    sd --fixed-strings ' @preview/tcdm:0.0.0 ' \
        {{ quote(' @preview/tcdm:' + version + ' ') }} \
        package/README.md

    sd --fixed-strings '#import "lib.typ":' \
        {{ quote('#import "@preview/tcdm:' + version + '":') }} \
        package/example/main.typ
    sd --fixed-strings 'json("/build/latest.json")' \
        'json(placeholder.latest-history-json)' \
        package/example/main.typ
    sd --fixed-strings 'yaml("/projects.yaml")' \
        'yaml(placeholder.projects-yaml)' \
        package/example/main.typ

    # 🎉 Successfully created the package/ directory.

# Build `build/index.html`
build-typ LANG="en":
    mkdir -p build
    uv run scripts/history_to_json.py > build/latest.json
    typst compile typ/main.typ build/index.html --root . --features html --input lang={{ LANG }}

# Build `build/pandoc.md` from `README.md` for `pandoc --from gfm`
build-for-pandoc:
    #!/usr/bin/env bash
    set -euxo pipefail

    mkdir -p build
    cd build

    # Write metadata
    cat > pandoc.md <<- "EOF"
    ---
    title: Best of Typst (TCDM)
    lang: en
    header-includes: |
        <style>
        details {
            margin-top: 1em;
        }
        li {
            margin-top: 0.2em;
        }
        .note {
            border-left: 0.25em solid #004daa;
            padding-left: 1em;
        }
        .note > .title {
            color: #004daa;
        }
        </style>
    ---
    EOF

    # Delete `<h1>` and unnecessary buttons
    cat ../README.md \
        | sed '1,5d' \
        | grep --invert-match '<a href="#contents">.* alt="Back to top"></a>' \
        >> pandoc.md
