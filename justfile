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

# Build `build/index.md` from `README.md` for `pandoc --from gfm`
build-for-pandoc:
    #!/usr/bin/env bash
    set -euxo pipefail

    rm -rf build
    mkdir -p build
    cd build

    # Write metadata
    cat > index.md <<- "EOF"
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
        >> index.md
