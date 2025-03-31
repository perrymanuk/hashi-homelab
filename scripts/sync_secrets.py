#!/usr/bin/env python3

import os
import sys
import logging
from github import Github, GithubException

# Constants
ENVRC_PATH = '/app/.envrc'  # Path inside the container
REPO_NAME = 'hashi-homelab' # Just the repo name

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_github_token():
    """Retrieves the GitHub token from the environment variable."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        logging.error("Error: GITHUB_TOKEN environment variable not set.")
        sys.exit(1)
    return token

def parse_envrc(filepath):
    """Parses the .envrc file and returns a dictionary of environment variables."""
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Basic parsing for 'export VAR=VALUE'
                if line.startswith('export '):
                    parts = line[len('export '):].split('=', 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        value = parts[1].strip()

                        # Remove surrounding quotes if present
                        if (value.startswith("'") and value.endswith("'")) or \
                           (value.startswith('"') and value.endswith('"')):
                            value = value[1:-1]

                        env_vars[name] = value
                    else:
                        logging.warning(f"Skipping malformed line: {line}")
                else:
                     logging.warning(f"Skipping line not starting with 'export ': {line}")

    except FileNotFoundError:
        logging.error(f"Error: Environment file not found at {filepath}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading environment file {filepath}: {e}")
        sys.exit(1)

    return env_vars

def main():
    """Main function to parse .envrc and sync secrets using PyGithub."""
    github_token = get_github_token()

    logging.info(f"Parsing environment variables from: {ENVRC_PATH}")
    env_vars = parse_envrc(ENVRC_PATH)

    if not env_vars:
        logging.info("No environment variables found in .envrc to sync.")
        sys.exit(0)

    logging.info(f"Found {len(env_vars)} variables. Attempting to sync to repository owned by the token user: {REPO_NAME}")

    try:
        g = Github(github_token)
        user = g.get_user()
        logging.info(f"Authenticated to GitHub as user: {user.login}")
        repo = user.get_repo(REPO_NAME)
        logging.info(f"Found repository: {repo.full_name}")

    except GithubException as e:
        logging.error(f"GitHub API Error during authentication or repo access: {e.status} {e.data.get('message', '')}")
        sys.exit(1)
    except Exception as e:
         logging.error(f"An unexpected error occurred during GitHub setup: {e}")
         sys.exit(1)


    success_count = 0
    failure_count = 0

    for name, value in env_vars.items():
        logging.info(f"Syncing secret: {name}...")
        try:
            repo.create_secret(name, value)
            logging.info(f"Secret '{name}' synced successfully.") # Corrected line 97
            success_count += 1
        except GithubException as e:
            logging.error(f"Failed to sync secret '{name}': {e.status} {e.data.get('message', '')}") # Corrected line 100
            failure_count += 1
        except Exception as e:
            logging.error(f"Failed to sync secret '{name}' with unexpected error: {e}") # Corrected line 103
            failure_count += 1

    logging.info("\n--- Sync Summary ---")
    logging.info(f"Successfully synced: {success_count}")
    logging.info(f"Failed to sync:    {failure_count}")

    if failure_count > 0:
        sys.exit(1) # Exit with error code if any secrets failed

if __name__ == "__main__":
    main()
