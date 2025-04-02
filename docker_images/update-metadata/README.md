# GitHub Secret Synchronization Script (Containerized)

## Purpose

This script (`sync_secrets.py`), running inside a Docker container, reads environment variables defined in the project's root `.envrc` file and synchronizes them as GitHub secrets to the `perrymanuk/hashi-homelab` repository using the `PyGithub` library.

## Requirements

*   **Docker:** Docker must be installed and running to build and execute the container.
*   **`NOMAD_VAR_github_pat` Environment Variable:** A GitHub Personal Access Token (PAT) with the `repo` scope must be available as an environment variable named `NOMAD_VAR_github_pat` in the **host shell** where you run the `make` command. The Makefile target (`sync-secrets`) will handle passing this token into the container under the name `GITHUB_TOKEN` for the script to use.
*   **`.envrc` File:** An `.envrc` file must exist at the project root (`/Users/perry.manuk/git/perrymanuk/hashi-homelab/.envrc`) containing the secrets to sync.

## Usage

1.  **Ensure `NOMAD_VAR_github_pat` is set:** Export your GitHub PAT in your current host shell session:
    ```bash
    export NOMAD_VAR_github_pat="your_github_pat_here"
    ```
2.  **Navigate to the project root directory:**
    ```bash
    cd /Users/perry.manuk/git/perrymanuk/hashi-homelab
    ```
3.  **Run the Makefile target:**
    ```bash
    make sync-secrets
    ```

This command will:
    *   Build the Docker image defined in `scripts/Dockerfile`.
    *   Run a container from the image.
    *   Mount the host's `.envrc` file into the container.
    *   Pass the **host's** `NOMAD_VAR_github_pat` environment variable into the container as `GITHUB_TOKEN`.
    *   Execute the `sync_secrets.py` script within the container.

The script will output the status of each secret synchronization attempt (created, updated, or failed).

**Important:** Running the script will overwrite any existing secrets in the GitHub repository that have the same name as variables found in the `.envrc` file.

## `.envrc` Format

The script expects the `.envrc` file to follow this format:

```bash
export VARIABLE_NAME=value
export ANOTHER_VARIABLE='value with spaces'
export YET_ANOTHER="double quoted value"
# This is a comment and will be ignored

# Empty lines are also ignored
export SECRET_KEY=a_very_secret_value_here
```

*   Lines must start with `export`.
*   Variable names and values are separated by `=`.
*   Values can be unquoted, single-quoted (`'...'`), or double-quoted (`"..."`). Quotes are stripped before syncing.
*   Lines starting with `#` (comments) and empty lines are ignored.
