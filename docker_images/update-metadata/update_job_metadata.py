
import argparse
import logging
import pathlib
import re
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_job_block(content):
    """Find the start and end indices of the main 'job' block."""
    job_match = re.search(r'^job\s+"[^"]+"\s*\{', content, re.MULTILINE)
    if not job_match:
        logging.warning("Could not find job block start.")
        return None, None

    start_index = job_match.start()
    # Find the matching closing brace
    brace_level = 0
    end_index = -1
    in_string = False
    escaped = False
    for i, char in enumerate(content[start_index:]):
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
                if brace_level == 0:
                    end_index = start_index + i
                    break

    if end_index == -1:
        logging.warning("Could not find matching closing brace for job block.")
        return None, None

    return start_index, end_index + 1

def find_meta_block(content):
    """Find the start and end indices of the 'meta' block within the given content."""
    meta_match = re.search(r'^\s*meta\s*\{', content, re.MULTILINE)
    if not meta_match:
        return None, None

    start_index = meta_match.start()
    # Find the matching closing brace
    brace_level = 0
    end_index = -1
    in_string = False
    escaped = False
    for i, char in enumerate(content[start_index:]):
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
                if brace_level == 0:
                    end_index = start_index + i
                    break

    if end_index == -1:
        logging.warning("Could not find matching closing brace for meta block.")
        return None, None

    return start_index, end_index + 1

def update_job_metadata(repo_root):
    """Finds Nomad job files and updates their meta block with job_file path."""
    repo_path = pathlib.Path(repo_root).resolve()
    nomad_jobs_path = repo_path / 'nomad_jobs'

    if not nomad_jobs_path.is_dir():
        logging.error(f"'nomad_jobs' directory not found in {repo_path}")
        sys.exit(1)

    logging.info(f"Scanning for job files in {nomad_jobs_path}...")

    job_files = list(nomad_jobs_path.rglob('*.nomad')) + list(nomad_jobs_path.rglob('*.job'))

    if not job_files:
        logging.warning("No *.nomad or *.job files found.")
        return

    modified_count = 0
    for job_file in job_files:
        try:
            relative_path = job_file.relative_to(repo_path).as_posix()
            logging.debug(f"Processing file: {relative_path}")
            content = job_file.read_text()
            original_content = content # Keep a copy for comparison

            job_start, job_end = find_job_block(content)
            if job_start is None or job_end is None:
                logging.warning(f"Skipping {relative_path}: Could not find main job block.")
                continue
            job_block_content = content[job_start:job_end]
            job_opening_line_match = re.match(r'^job\s+"[^"]+"\s*\{\s*\n?', job_block_content, re.MULTILINE)
            if not job_opening_line_match:
                 logging.warning(f"Skipping {relative_path}: Could not match job opening line format.")
                 continue
            job_insert_pos = job_start + job_opening_line_match.end()

            meta_start_rel, meta_end_rel = find_meta_block(job_block_content)
            new_job_file_line = f'  job_file = "{relative_path}"'
            modified = False

            if meta_start_rel is not None and meta_end_rel is not None:
                meta_start_abs = job_start + meta_start_rel
                meta_end_abs = job_start + meta_end_rel
                meta_block_content = content[meta_start_abs:meta_end_abs]
                meta_opening_line_match = re.match(r'^\s*meta\s*\{\s*\n?', meta_block_content, re.MULTILINE)
                if not meta_opening_line_match:
                    logging.warning(f"Skipping {relative_path}: Could not match meta opening line format.")
                    continue
                meta_insert_pos = meta_start_abs + meta_opening_line_match.end()

                job_file_line_match = re.search(r'^(\s*)job_file\s*=\s*".*?"$\n?', meta_block_content, re.MULTILINE)

                if job_file_line_match:
                    existing_line = job_file_line_match.group(0)
                    indent = job_file_line_match.group(1)
                    new_line_with_indent = f'{indent}job_file = "{relative_path}"\n' # Ensure newline
                    if existing_line.strip() != new_line_with_indent.strip():
                         # Replace existing line
                        start = meta_start_abs + job_file_line_match.start()
                        end = meta_start_abs + job_file_line_match.end()
                        # Ensure we capture the trailing newline if present in match
                        content = content[:start] + new_line_with_indent + content[end:]
                        modified = True
                else:
                    # Insert new job_file line inside meta block
                    content = content[:meta_insert_pos] + new_job_file_line + '\n' + content[meta_insert_pos:]
                    modified = True
            else:
                # Insert new meta block
                new_meta_block = f'\n  meta {{\n{new_job_file_line}\n  }}\n'
                content = content[:job_insert_pos] + new_meta_block + content[job_insert_pos:]
                modified = True

            if modified and content != original_content:
                job_file.write_text(content)
                logging.info(f"Updated metadata in: {relative_path}")
                modified_count += 1
            elif not modified:
                 logging.debug(f"No changes needed for: {relative_path}")

        except Exception as e:
            logging.error(f"Failed to process {relative_path}: {e}")

    logging.info(f"Metadata update complete. {modified_count} files modified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Nomad job files with job_file metadata.")
    # Default to the parent directory of the script's directory (../)
    script_dir = pathlib.Path(__file__).parent.resolve()
    default_repo_root = script_dir.parent
    parser.add_argument(
        "--repo-root",
        type=str,
        default=str(default_repo_root),
        help="Path to the root of the repository."
    )
    args = parser.parse_args()

    update_job_metadata(args.repo_root)

