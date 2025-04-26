#!/usr/bin/env python3
import requests
import json
import argparse
import sys
from tabulate import tabulate
from colorama import Fore, Style, init

init()  # Initialize colorama

def get_headers(token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Nomad-Token"] = token
    return headers

def get_running_allocations(base_url, token=None, debug=False, node_id=None):
    """Get all running allocations from Nomad, optionally filtered by node_id"""
    try:
        # Build URL with optional node filter
        url = f"{base_url}/v1/allocations"
        if node_id:
            url = f"{base_url}/v1/node/{node_id}/allocations"
            if debug:
                print(f"Fetching allocations for node {node_id}")
        
        response = requests.get(
            url,
            headers=get_headers(token)
        )
        
        if response.status_code != 200:
            print(f"Error fetching allocations: {response.status_code}")
            print(response.text)
            return []
        
        allocations = response.json()
        
        # Filter to only running allocations
        running_allocs = [a for a in allocations if a.get("ClientStatus") == "running"]
        
        if debug:
            print(f"Found {len(running_allocs)} running allocations out of {len(allocations)} total")
            
        return running_allocs
    except Exception as e:
        print(f"Error fetching allocations: {e}")
        return []

def get_node_address(base_url, node_id, token=None, debug=False):
    """Get the HTTP address of a specific Nomad client node"""
    try:
        response = requests.get(
            f"{base_url}/v1/node/{node_id}",
            headers=get_headers(token)
        )
        
        if response.status_code != 200:
            if debug:
                print(f"Error fetching node {node_id}: {response.status_code}")
            return None
            
        node_data = response.json()
        
        # Try to find the HTTP address in the node's attributes
        http_addr = node_data.get("HTTPAddr")
        
        if not http_addr:
            # Try to find in meta
            meta = node_data.get("Meta", {})
            if "connect.gateway.proxy.addr" in meta:
                http_addr = meta["connect.gateway.proxy.addr"]
                
        if debug and http_addr:
            print(f"Found node address for {node_id}: {http_addr}")
            
        return http_addr
    except Exception as e:
        if debug:
            print(f"Error fetching node address: {e}")
        return None

def get_allocation_stats(base_url, node_address, alloc_id, token=None, debug=False):
    """Get detailed statistics for an allocation, trying different endpoints"""
    # First try the client allocation stats endpoint directly
    try:
        # If we have a node address, try to use it
        if node_address:
            url = f"http://{node_address}/v1/client/allocation/{alloc_id}/stats"
        else:
            # Otherwise fall back to the provided base URL
            url = f"{base_url}/v1/client/allocation/{alloc_id}/stats"
            
        if debug:
            print(f"Requesting stats from {url}")
            
        response = requests.get(
            url,
            headers=get_headers(token)
        )
        
        if response.status_code == 200:
            return response.json()
        elif debug:
            print(f"Error fetching stats from {url}: {response.status_code}")
    except Exception as e:
        if debug:
            print(f"Error fetching allocation stats: {e}")
    
    # If direct client stats failed, try the allocation endpoint
    try:
        response = requests.get(
            f"{base_url}/v1/allocation/{alloc_id}",
            headers=get_headers(token)
        )
        
        if response.status_code == 200:
            return {"allocation": response.json()}
        elif debug:
            print(f"Error fetching allocation {alloc_id}: {response.status_code}")
    except Exception as e:
        if debug:
            print(f"Error fetching allocation: {e}")
    
    return None

def get_job_info(base_url, job_id, token=None, debug=False):
    """Get detailed job information"""
    try:
        response = requests.get(
            f"{base_url}/v1/job/{job_id}",
            headers=get_headers(token)
        )
        
        if response.status_code != 200:
            if debug:
                print(f"Error fetching job {job_id}: {response.status_code}")
            return None
            
        return response.json()
    except Exception as e:
        if debug:
            print(f"Error fetching job info: {e}")
        return None

def extract_memory_usage(stats, alloc, job_info, task_name, debug=False):
    """Extract memory usage information from various possible locations in the API response"""
    memory_usage_mb = 0
    allocated_mb = 0
    
    # First, try to get the allocated memory from job info - most accurate source
    if job_info:
        try:
            # Extract the allocated memory from the job specification
            for task_group in job_info.get("TaskGroups", []):
                if task_group.get("Name") == alloc.get("TaskGroup"):
                    for task in task_group.get("Tasks", []):
                        if task.get("Name") == task_name:
                            resources = task.get("Resources", {})
                            allocated_mb = resources.get("MemoryMB", 0)
                            if debug:
                                print(f"Found allocated memory from job info: {allocated_mb} MB")
                            break
        except Exception as e:
            if debug:
                print(f"Error extracting memory from job info: {e}")
    
    # If we still don't have allocated memory, try getting it from the allocation
    if allocated_mb == 0:
        try:
            # New Nomad version uses AllocatedResources
            allocated_resources = alloc.get("AllocatedResources", {}).get("Tasks", {}).get(task_name, {})
            memory = allocated_resources.get("Memory", {})
            allocated_mb = memory.get("MemoryMB", 0)
            
            # Older versions used TaskResources
            if allocated_mb == 0:
                task_resources = alloc.get("TaskResources", {}).get(task_name, {})
                allocated_mb = task_resources.get("MemoryMB", 0)
            
            if debug and allocated_mb > 0:
                print(f"Found allocated memory from allocation: {allocated_mb} MB")
        except Exception as e:
            if debug:
                print(f"Error extracting allocated memory: {e}")
    
    # Now try to get the actual usage from multiple possible paths
    if stats:
        try:
            # Dump entire stats structure for deep debugging if enabled
            if debug and debug > 1:  # Extra verbose debug
                print(f"Complete stats for {task_name}:")
                print(json.dumps(stats, indent=2)[:2000])  # Print first 2000 chars
            
            # First check for Usage directly in MemoryStats (based on your output)
            if "ResourceUsage" in stats and "MemoryStats" in stats.get("ResourceUsage", {}):
                memory_stats = stats.get("ResourceUsage", {}).get("MemoryStats", {})
                usage_bytes = memory_stats.get("Usage", 0)
                if usage_bytes > 0:
                    memory_usage_mb = usage_bytes / (1024 * 1024)
                    if debug:
                        print(f"Found memory usage from top-level ResourceUsage.MemoryStats.Usage: {memory_usage_mb} MB")
            
            # If we still don't have memory usage, try other paths
            if memory_usage_mb == 0 and "Tasks" in stats:
                task_stats = stats.get("Tasks", {}).get(task_name, {})
                
                # Check for direct Usage in MemoryStats
                memory_stats = task_stats.get("ResourceUsage", {}).get("MemoryStats", {})
                if memory_stats:
                    usage_bytes = memory_stats.get("Usage", 0)
                    if usage_bytes > 0:
                        memory_usage_mb = usage_bytes / (1024 * 1024)
                        if debug:
                            print(f"Found memory usage from ResourceUsage.MemoryStats.Usage: {memory_usage_mb} MB")
                
                # If not found yet, try Memory path
                if memory_usage_mb == 0:
                    memory = task_stats.get("ResourceUsage", {}).get("Memory", {})
                    if memory:
                        # Try Usage field first
                        usage_bytes = memory.get("Usage", 0)
                        if usage_bytes > 0:
                            memory_usage_mb = usage_bytes / (1024 * 1024)
                            if debug:
                                print(f"Found memory usage from ResourceUsage.Memory.Usage: {memory_usage_mb} MB")
                        
                        # If not found, try RSS
                        if memory_usage_mb == 0:
                            rss_bytes = memory.get("RSS", 0)
                            if rss_bytes > 0:
                                memory_usage_mb = rss_bytes / (1024 * 1024)
                                if debug:
                                    print(f"Found memory usage from ResourceUsage.Memory.RSS: {memory_usage_mb} MB")
                
                # Docker stats path - more accurate for Docker driver tasks
                if memory_usage_mb == 0 and "Stats" in task_stats:
                    docker_stats = task_stats.get("Stats", {})
                    if "memory_stats" in docker_stats:
                        # Docker stats usually reports in bytes
                        memory_usage_bytes = docker_stats.get("memory_stats", {}).get("usage", 0)
                        
                        # Some Docker implementations include cache in usage, so we should subtract it if available
                        cache_bytes = docker_stats.get("memory_stats", {}).get("stats", {}).get("cache", 0)
                        actual_usage = memory_usage_bytes - cache_bytes
                        
                        if actual_usage > 0:
                            memory_usage_mb = actual_usage / (1024 * 1024)
                            if debug:
                                print(f"Found memory usage from Docker stats: {memory_usage_mb} MB")
            
            # For allocation-only stats (when client stats endpoint failed)
            if memory_usage_mb == 0 and "allocation" in stats:
                alloc_data = stats.get("allocation", {})
                # This likely won't have actual usage, just allocation, but we check anyway
                if "TaskStates" in alloc_data:
                    task_state = alloc_data.get("TaskStates", {}).get(task_name, {})
                    # Task state might have resource usage in newer Nomad versions
                    if "ResourceUsage" in task_state:
                        memory_stats = task_state.get("ResourceUsage", {}).get("MemoryStats", {})
                        usage_bytes = memory_stats.get("Usage", 0) or memory_stats.get("RSS", 0)
                        if usage_bytes > 0:
                            memory_usage_mb = usage_bytes / (1024 * 1024)
                            if debug:
                                print(f"Found memory usage from allocation TaskStates: {memory_usage_mb} MB")
            
            # For debugging: if we still don't have memory usage, print out the stats structure
            if memory_usage_mb == 0 and debug:
                print(f"Could not find memory usage in stats for task {task_name}")
                if "Tasks" in stats and task_name in stats.get("Tasks", {}):
                    task_stats = stats.get("Tasks", {}).get(task_name, {})
                    print(f"Available task_stats keys: {list(task_stats.keys())}")
                    
                    # Try to find any memory related keys
                    if "ResourceUsage" in task_stats:
                        resource_usage = task_stats.get("ResourceUsage", {})
                        print(f"ResourceUsage keys: {list(resource_usage.keys())}")
                        
                        # If we find Memory in ResourceUsage, print its contents
                        if "Memory" in resource_usage:
                            memory = resource_usage.get("Memory", {})
                            print(f"Memory keys: {list(memory.keys())}")
                            print(f"Memory values: {memory}")
                        
                        # If we find MemoryStats in ResourceUsage, print its contents
                        if "MemoryStats" in resource_usage:
                            memory_stats = resource_usage.get("MemoryStats", {})
                            print(f"MemoryStats keys: {list(memory_stats.keys())}")
                            print(f"MemoryStats values: {memory_stats}")
                
        except Exception as e:
            if debug:
                print(f"Error extracting memory usage: {str(e)}")
                import traceback
                traceback.print_exc()
    
    return allocated_mb, memory_usage_mb

def analyze_memory_usage(base_url, threshold=0.6, token=None, debug=False, node_id=None):
    """Analyze memory usage across all running allocations"""
    allocations = get_running_allocations(base_url, token, debug, node_id)
    
    if debug:
        print(f"Processing {len(allocations)} allocations...")
    
    results = []
    node_addresses = {}  # Cache node addresses
    job_cache = {}  # Cache job info
    
    for alloc in allocations:
        alloc_id = alloc.get("ID")
        job_id = alloc.get("JobID")
        task_group = alloc.get("TaskGroup")
        node_id = alloc.get("NodeID")
        node_name = alloc.get("NodeName", "unknown")
        
        if debug:
            print(f"\nProcessing allocation {alloc_id[:8]} for job {job_id}...")
        
        # Get node address (for direct stats access)
        if node_id not in node_addresses:
            node_addresses[node_id] = get_node_address(base_url, node_id, token, debug)
        
        node_address = node_addresses.get(node_id)
        
        # Get job info (only once per job)
        if job_id not in job_cache:
            job_cache[job_id] = get_job_info(base_url, job_id, token, debug)
        
        job_info = job_cache.get(job_id)
        
        # Get allocation stats - direct access to client node is most accurate
        stats = get_allocation_stats(base_url, node_address, alloc_id, token, debug)
        
        if not stats and debug:
            print(f"No stats found for allocation {alloc_id}")
            
        # Get task list - first from stats, then from allocation if needed
        task_names = []
        if stats and "Tasks" in stats:
            task_names = list(stats.get("Tasks", {}).keys())
        
        # If no tasks found in stats, try to get from allocation
        if not task_names:
            # Try different places in the allocation to find tasks
            if "TaskStates" in alloc:
                task_names = list(alloc.get("TaskStates", {}).keys())
            elif "AllocatedResources" in alloc and "Tasks" in alloc.get("AllocatedResources", {}):
                task_names = list(alloc.get("AllocatedResources", {}).get("Tasks", {}).keys())
            elif "TaskResources" in alloc:
                task_names = list(alloc.get("TaskResources", {}).keys())
            
        if debug:
            print(f"Found tasks: {task_names}")
            
        # Process each task
        for task_name in task_names:
            allocated_mb, memory_usage_mb = extract_memory_usage(stats, alloc, job_info, task_name, debug)
            
            # Calculate usage percentage
            if allocated_mb > 0 and memory_usage_mb > 0:
                usage_percentage = memory_usage_mb / allocated_mb
            else:
                usage_percentage = 0
                
            results.append({
                "job_id": job_id,
                "task_group": task_group,
                "task_name": task_name,
                "node": node_name,
                "alloc_id": alloc_id[:8],  # Shortened ID
                "allocated_mb": allocated_mb,
                "used_mb": round(memory_usage_mb, 2),
                "usage_percentage": round(usage_percentage * 100, 2),
                "below_threshold": usage_percentage < threshold
            })
    
    # Sort by usage percentage, ascending (lowest usage first)
    results.sort(key=lambda x: x["usage_percentage"])
    
    return results

def print_table(results, threshold=0.6):
    """Print a table of memory usage data"""
    table_data = []
    
    for r in results:
        # Color rows below threshold in yellow
        if r["below_threshold"] and r["allocated_mb"] > 0:  # Only highlight rows with actual memory allocated
            row_style = Fore.YELLOW
        else:
            row_style = ""
            
        row = [
            f"{row_style}{r['job_id']}{Style.RESET_ALL}",
            f"{row_style}{r['task_group']}{Style.RESET_ALL}",
            f"{row_style}{r['task_name']}{Style.RESET_ALL}",
            f"{row_style}{r['node']}{Style.RESET_ALL}",
            f"{row_style}{r['alloc_id']}{Style.RESET_ALL}",
            f"{row_style}{r['allocated_mb']}{Style.RESET_ALL}",
            f"{row_style}{r['used_mb']}{Style.RESET_ALL}",
            f"{row_style}{r['usage_percentage']}%{Style.RESET_ALL}",
        ]
        table_data.append(row)
    
    headers = ["Job", "Task Group", "Task", "Node", "Alloc ID", "Allocated MB", "Used MB", "Usage %"]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Filter out allocations with 0 allocated memory for the summary
    valid_results = [r for r in results if r["allocated_mb"] > 0]
    below_threshold = [r for r in valid_results if r["below_threshold"]]
    
    print(f"\nFound {len(below_threshold)} allocations using less than {threshold*100}% of allocated memory")
    
    # Calculate total waste
    total_allocated = sum(r["allocated_mb"] for r in below_threshold)
    total_used = sum(r["used_mb"] for r in below_threshold)
    total_waste = total_allocated - total_used
    
    print(f"Total memory that could be reclaimed: {round(total_waste, 2)} MB")

def main():
    parser = argparse.ArgumentParser(description="Analyze Nomad memory usage")
    parser.add_argument("--nomad", default="http://localhost:4646", help="Nomad API address")
    parser.add_argument("--token", help="Nomad ACL token")
    parser.add_argument("--threshold", type=float, default=0.6, help="Memory usage threshold (default: 0.6 or 60%)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--verbose-debug", action="store_true", help="Enable extra verbose debug output")
    parser.add_argument("--region", help="Nomad region")
    parser.add_argument("--node", help="Specific node to target")
    
    args = parser.parse_args()
    
    # If region is specified, add it to the URL
    base_url = args.nomad
    if args.region:
        if "?" in base_url:
            base_url = f"{base_url}&region={args.region}"
        else:
            base_url = f"{base_url}?region={args.region}"
    
    # Set debug level 
    debug_level = 0
    if args.debug:
        debug_level = 1
        print(f"Using Nomad API at {base_url}")
    if args.verbose_debug:
        debug_level = 2
    
    results = analyze_memory_usage(base_url, args.threshold, args.token, debug_level, args.node)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_table(results, args.threshold)

if __name__ == "__main__":
    main()