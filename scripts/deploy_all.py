#!/usr/bin/env python3
import os
import subprocess
import json
import argparse
import sys
import yaml
import glob
import re

def extract_job_paths_from_workflows():
    """Extract job paths from GitHub workflow files"""
    workflow_paths = []
    
    # Find all GitHub workflow files
    for workflow_file in glob.glob(".github/workflows/*.y*ml"):
        with open(workflow_file, 'r') as file:
            try:
                # Parse YAML content
                workflow = yaml.safe_load(file)
                
                # Look for the filters section with nomadjobs paths
                if workflow and 'jobs' in workflow:
                    for job_name, job_config in workflow['jobs'].items():
                        if 'steps' in job_config:
                            for step in job_config['steps']:
                                # Look for dorny/paths-filter step
                                if step.get('uses', '').startswith('dorny/paths-filter'):
                                    with_config = step.get('with', {})
                                    if 'filters' in with_config:
                                        filters_str = with_config['filters']
                                        # Extract paths from the filters string using regex
                                        nomadjobs_section = re.search(r'nomadjobs:.*?(?=\w+:|$)', filters_str, re.DOTALL)
                                        if nomadjobs_section:
                                            paths = re.findall(r"'([^']*\.job)'", nomadjobs_section.group(0))
                                            workflow_paths.extend(paths)
                                        
                                        # Also look for any patterns quoted with single quotes
                                        additional_paths = re.findall(r"'([^']*\.job)'", filters_str)
                                        workflow_paths.extend(additional_paths)
                                        
                                        # Also look for volume paths
                                        volume_section = re.search(r'volumes:.*?(?=\w+:|$)', filters_str, re.DOTALL)
                                        if volume_section:
                                            volume_paths = re.findall(r"'([^']*)'", volume_section.group(0))
                                            for path in volume_paths:
                                                if 'volume.hcl' in path:
                                                    workflow_paths.append(path)
            except yaml.YAMLError:
                # If YAML parsing fails, try to extract patterns using regex
                file.seek(0)  # Reset file pointer to the beginning
                content = file.read()
                
                nomadjobs_patterns = re.findall(r"'(nomad_jobs/[^']*\.job)'", content)
                workflow_paths.extend(nomadjobs_patterns)
                
                volume_patterns = re.findall(r"'(nomad_jobs/[^']*volume\.hcl)'", content)
                workflow_paths.extend(volume_patterns)
    
    # Add fallback paths in case we can't extract from workflows
    fallback_paths = [
        'nomad_jobs/**/volume.hcl',
        'nomad_jobs/**/*.job',
    ]
    
    # If no paths were found in workflows, use fallback paths
    if not workflow_paths:
        print("Warning: Could not extract job paths from workflows. Using fallback patterns.")
        return fallback_paths
    
    # Deduplicate paths
    return list(set(workflow_paths))

def find_job_files(patterns):
    """Find all job files matching the given patterns"""
    job_files = set()
    for pattern in patterns:
        # Handle glob patterns
        if "*" in pattern:
            matches = glob.glob(pattern, recursive=True)
            job_files.update(matches)
        elif os.path.exists(pattern):
            job_files.add(pattern)
    return sorted(list(job_files))

def find_volume_files(patterns):
    """Find all volume files matching the given patterns"""
    volume_files = set()
    for pattern in patterns:
        # Check if this is a volume pattern
        if "volume" in pattern.lower():
            # Handle glob patterns with recursive search
            if "**" in pattern:
                matches = glob.glob(pattern, recursive=True)
                volume_files.update(matches)
            else:
                matches = glob.glob(pattern)
                volume_files.update(matches)
    return sorted(list(volume_files))

def deploy_job(job_file, nomad_addr, env_vars, dry_run=False, verbose=False):
    """Deploy a single Nomad job"""
    if verbose:
        print(f"Deploying {job_file}...")
    
    cmd = ["nomad", "job", "run", job_file]
    
    # Copy the environment variables and add NOMAD_ADDR
    env = os.environ.copy()
    env.update(env_vars)
    env["NOMAD_ADDR"] = nomad_addr
    
    if dry_run:
        print(f"Would run: {' '.join(cmd)}")
        return True
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            if verbose:
                print(f"Successfully deployed {job_file}")
                print(result.stdout)
            else:
                print(f"Successfully deployed {job_file}")
            return True
        else:
            print(f"Failed to deploy {job_file}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error deploying {job_file}: {e}")
        return False

def create_volume(volume_file, nomad_addr, env_vars, dry_run=False, verbose=False):
    """Create a Nomad volume"""
    if verbose:
        print(f"Creating volume from {volume_file}...")
    
    cmd = ["nomad", "volume", "create", volume_file]
    
    # Copy the environment variables and add NOMAD_ADDR
    env = os.environ.copy()
    env.update(env_vars)
    env["NOMAD_ADDR"] = nomad_addr
    
    if dry_run:
        print(f"Would run: {' '.join(cmd)}")
        return True
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            if verbose:
                print(f"Successfully created volume from {volume_file}")
                print(result.stdout)
            else:
                print(f"Successfully created volume from {volume_file}")
            return True
        else:
            print(f"Failed to create volume from {volume_file}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error creating volume from {volume_file}: {e}")
        return False

def load_env_from_envrc():
    """Load environment variables from .envrc file"""
    env_vars = {}
    envrc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "envrc")
    
    if os.path.exists(envrc_path):
        with open(envrc_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if "export" in line:
                        line = line.replace("export ", "")
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        # Strip quotes if present
                        value = value.strip("'\"")
                        # Convert to NOMAD_VAR_ format
                        if not key.startswith("NOMAD_VAR_"):
                            nomad_key = f"NOMAD_VAR_{key.lower()}"
                            env_vars[nomad_key] = value
                        else:
                            env_vars[key] = value
    return env_vars

def main():
    parser = argparse.ArgumentParser(description="Deploy Nomad jobs and volumes based on GitHub workflow")
    parser.add_argument("--nomad", default="http://localhost:4646", help="Nomad API address")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually deploy, just show what would be done")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--skip-volumes", action="store_true", help="Skip volume creation")
    parser.add_argument("--jobs-only", action="store_true", help="Only deploy jobs, don't create volumes")
    parser.add_argument("--volumes-only", action="store_true", help="Only create volumes, don't deploy jobs")
    parser.add_argument("--only", help="Only deploy jobs matching this pattern (e.g., 'redis' or 'storage')")
    
    args = parser.parse_args()
    
    # Get environment variables from envrc file
    env_vars = load_env_from_envrc()
    
    if not env_vars and not args.dry_run:
        print("Warning: No environment variables found in envrc file.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Set default environment variables if not provided
    default_vars = {
        "NOMAD_VAR_region": "home",
        "NOMAD_VAR_tld": os.environ.get("NOMAD_VAR_tld", "home.lab"),
        "NOMAD_VAR_shared_dir": "/home/shared/",
        "NOMAD_VAR_downloads_dir": "/home/sabnzbd/downloads",
        "NOMAD_VAR_media_dir": "/home/media",
        "NOMAD_VAR_movies_dir": "/home/media/Movies",
        "NOMAD_VAR_tv_dir": "/home/media/TV",
        "NOMAD_VAR_music_dir": "/home/media/Music",
        "NOMAD_VAR_books_dir": "/home/media/Books",
        "NOMAD_VAR_datacenter": "dc1",
        "NOMAD_VAR_dns_server_ip": "192.168.50.2"
    }
    
    # Only add default vars if not already present
    for key, value in default_vars.items():
        if key not in env_vars:
            env_vars[key] = value
    
    # Extract job paths from GitHub workflow files
    all_patterns = extract_job_paths_from_workflows()
    
    # Separate volume patterns from job patterns
    volume_patterns = [p for p in all_patterns if "volume" in p.lower()]
    job_patterns = [p for p in all_patterns if p.endswith(".job")]
    
    print(f"Found {len(job_patterns)} job patterns and {len(volume_patterns)} volume patterns in GitHub workflows")
    
    # Deploy volumes first (unless skipped)
    if not args.jobs_only and not args.skip_volumes:
        volume_files = find_volume_files(volume_patterns)
        if args.only:
            volume_files = [vf for vf in volume_files if args.only in vf]
        
        print(f"Found {len(volume_files)} volume files")
        
        if not volume_files:
            print("No volume files found. Skipping volume creation.")
        else:
            success_count = 0
            for volume_file in volume_files:
                if create_volume(volume_file, args.nomad, env_vars, args.dry_run, args.verbose):
                    success_count += 1
            
            print(f"Created {success_count} out of {len(volume_files)} volumes")
    
    # Deploy jobs (unless only creating volumes)
    if not args.volumes_only:
        job_files = find_job_files(job_patterns)
        if args.only:
            job_files = [jf for jf in job_files if args.only in jf]
        
        print(f"Found {len(job_files)} job files")
        
        if not job_files:
            print("No job files found to deploy.")
        else:
            success_count = 0
            for job_file in job_files:
                if deploy_job(job_file, args.nomad, env_vars, args.dry_run, args.verbose):
                    success_count += 1
            
            print(f"Deployed {success_count} out of {len(job_files)} jobs")

if __name__ == "__main__":
    main()