#!/usr/bin/env python3
"""
Simple GitHub Actions Status Monitor

Monitors the current GitHub Actions workflow status.
"""

import subprocess
import json
import time
import sys

def check_workflow_status():
    """Check the current workflow status"""
    try:
        cmd = [
            "gh", "run", "list", 
            "--repo", "puneetrinity/ubiquitous-octo-invention",
            "--limit", "1",
            "--json", "conclusion,status,workflowName,createdAt,url,headBranch"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            runs = json.loads(result.stdout)
            if runs:
                return runs[0]
            else:
                return None
        else:
            print(f"Error: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("GitHub CLI (gh) not found. Install from: https://cli.github.com/")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def format_status(run_info):
    """Format the status information"""
    if not run_info:
        return "No workflow runs found"
    
    status_emoji = {
        'completed': '✅' if run_info.get('conclusion') == 'success' else '❌',
        'in_progress': '🔄',
        'queued': '⏳'
    }
    
    status = run_info['status']
    conclusion = run_info.get('conclusion', 'N/A')
    
    emoji = status_emoji.get(status, '❓')
    
    info = [
        f"{emoji} Workflow: {run_info['workflowName']}",
        f"   Branch: {run_info.get('headBranch', 'N/A')}",
        f"   Status: {status}",
        f"   Conclusion: {conclusion}",
        f"   Created: {run_info['createdAt']}",
        f"   URL: {run_info['url']}"
    ]
    
    return '\n'.join(info)

def monitor_workflow(interval=30, max_checks=20):
    """Monitor workflow status with periodic updates"""
    print("🔍 Monitoring GitHub Actions workflow...")
    print(f"   Checking every {interval} seconds")
    print(f"   Max checks: {max_checks}")
    print("-" * 50)
    
    for i in range(max_checks):
        run_info = check_workflow_status()
        
        print(f"\n[Check {i+1}/{max_checks}]")
        print(format_status(run_info))
        
        if run_info and run_info['status'] == 'completed':
            conclusion = run_info.get('conclusion')
            if conclusion == 'success':
                print("\n🎉 Workflow completed successfully!")
                print("✅ Docker image should now be available in the registry")
                print("\n📋 Next steps:")
                print("1. Deploy on RunPod")
                print("2. Set environment variables")
                print("3. Test the API")
                return True
            else:
                print(f"\n❌ Workflow failed with conclusion: {conclusion}")
                print("💡 Check the workflow logs for details")
                return False
        
        if i < max_checks - 1:  # Don't sleep on the last iteration
            print(f"\n⏳ Waiting {interval} seconds for next check...")
            time.sleep(interval)
    
    print(f"\n⏰ Reached maximum number of checks ({max_checks})")
    print("💡 Continue monitoring manually or run the script again")
    return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print("Invalid interval. Using default of 30 seconds.")
            interval = 30
    else:
        interval = 30
    
    # First, do an immediate check
    print("🚀 Initial workflow status check:")
    run_info = check_workflow_status()
    print(format_status(run_info))
    
    if run_info and run_info['status'] in ['in_progress', 'queued']:
        print(f"\n🔄 Workflow is {run_info['status']}. Starting monitoring...")
        monitor_workflow(interval)
    elif run_info and run_info['status'] == 'completed':
        conclusion = run_info.get('conclusion')
        if conclusion == 'success':
            print("\n✅ Workflow already completed successfully!")
        else:
            print(f"\n❌ Workflow completed with status: {conclusion}")
    else:
        print("\n❓ No active workflow found")

if __name__ == "__main__":
    main()
