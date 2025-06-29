#!/usr/bin/env python3
"""
RunPod Deployment Troubleshooting Script

This script helps diagnose and fix issues with RunPod deployment,
including GitHub Actions, Docker registry permissions, and environment setup.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

class RunPodDeploymentTroubleshooter:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.github_repo = "puneetrinity/ubiquitous-octo-invention"
        self.registry = "ghcr.io"
        self.image_name = f"{self.registry}/{self.github_repo}"
        
    def check_github_actions_status(self) -> Dict:
        """Check the status of the latest GitHub Actions workflow"""
        print("🔍 Checking GitHub Actions workflow status...")
        
        try:
            # Get the latest workflow run
            cmd = [
                "gh", "run", "list", 
                "--repo", self.github_repo,
                "--limit", "1",
                "--json", "conclusion,status,workflowName,createdAt,url"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode == 0:
                runs = json.loads(result.stdout)
                if runs:
                    latest_run = runs[0]
                    print(f"✅ Latest workflow: {latest_run['workflowName']}")
                    print(f"   Status: {latest_run['status']}")
                    print(f"   Conclusion: {latest_run.get('conclusion', 'N/A')}")
                    print(f"   Created: {latest_run['createdAt']}")
                    print(f"   URL: {latest_run['url']}")
                    return latest_run
                else:
                    print("❌ No workflow runs found")
                    return {}
            else:
                print(f"❌ Failed to get workflow status: {result.stderr}")
                return {}
                
        except FileNotFoundError:
            print("❌ GitHub CLI (gh) not found. Please install it to check workflow status.")
            print("   Install from: https://cli.github.com/")
            return {}
        except Exception as e:
            print(f"❌ Error checking workflow status: {e}")
            return {}
    
    def check_container_registry_permissions(self) -> bool:
        """Check if we can access the container registry"""
        print("🔍 Checking container registry permissions...")
        
        try:
            # Try to list packages (requires read permission)
            cmd = [
                "gh", "api", 
                f"/user/packages?package_type=container",
                "--jq", ".[] | select(.name | contains(\"ubiquitous-octo-invention\"))"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print("✅ Container registry access confirmed")
                    print("✅ Package exists in registry")
                    return True
                else:
                    print("⚠️  Registry accessible but no package found yet")
                    return True
            else:
                print(f"❌ Cannot access container registry: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ GitHub CLI (gh) not found")
            return False
        except Exception as e:
            print(f"❌ Error checking registry permissions: {e}")
            return False
    
    def check_repository_settings(self) -> Dict:
        """Check repository settings that affect Actions and packages"""
        print("🔍 Checking repository settings...")
        
        settings = {}
        
        try:
            # Check if Actions are enabled
            cmd = ["gh", "api", f"/repos/{self.github_repo}", "--jq", ".has_issues,.has_projects,.has_wiki"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check package permissions
            cmd_perms = ["gh", "api", f"/repos/{self.github_repo}", "--jq", ".permissions"]
            result_perms = subprocess.run(cmd_perms, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Repository accessible")
                settings['accessible'] = True
            else:
                print("❌ Cannot access repository")
                settings['accessible'] = False
                
        except Exception as e:
            print(f"❌ Error checking repository settings: {e}")
            settings['error'] = str(e)
            
        return settings
    
    def check_docker_image_availability(self) -> bool:
        """Check if the Docker image was successfully built and pushed"""
        print("🔍 Checking Docker image availability...")
        
        try:
            # Try to pull the latest image
            cmd = ["docker", "pull", f"{self.image_name}:latest"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Docker image successfully pulled")
                return True
            else:
                print(f"❌ Cannot pull Docker image: {result.stderr}")
                
                # Check if it's an authentication issue
                if "authentication required" in result.stderr.lower():
                    print("💡 Authentication required. Try logging in:")
                    print(f"   docker login {self.registry}")
                    
                return False
                
        except FileNotFoundError:
            print("❌ Docker not found. Please install Docker.")
            return False
        except Exception as e:
            print(f"❌ Error checking Docker image: {e}")
            return False
    
    def generate_runpod_deployment_commands(self) -> List[str]:
        """Generate commands for RunPod deployment"""
        print("📋 Generating RunPod deployment commands...")
        
        commands = [
            "# RunPod Deployment Commands",
            "",
            "# 1. Pull the latest Docker image",
            f"docker pull {self.image_name}:latest",
            "",
            "# 2. Run the container with RunPod environment variables",
            "docker run -d \\",
            f"  --name ai-search-system \\",
            "  -p 8000:8000 \\",
            "  -e RUNPOD_POD_ID=$RUNPOD_POD_ID \\",
            "  -e RUNPOD_TCP_PORT_8000=$RUNPOD_TCP_PORT_8000 \\",
            "  -e OLLAMA_BASE_URL=http://localhost:11434 \\",
            "  -e MODEL_CACHE_DIR=/app/cache \\",
            "  -e LOG_LEVEL=INFO \\",
            f"  {self.image_name}:latest",
            "",
            "# 3. Check container status",
            "docker ps",
            "docker logs ai-search-system",
            "",
            "# 4. Test the API",
            "curl -X POST http://localhost:8000/api/chat \\",
            "  -H 'Content-Type: application/json' \\",
            "  -d '{\"message\": \"Hello, test the AI system\", \"stream\": false}'",
            "",
            "# 5. Run the final fix script inside the container (if needed)",
            "docker exec ai-search-system python scripts/final-runpod-fix.py",
        ]
        
        return commands
    
    def create_runpod_troubleshooting_guide(self) -> None:
        """Create a comprehensive troubleshooting guide for RunPod"""
        guide_path = self.repo_path / "RUNPOD_TROUBLESHOOTING.md"
        
        guide_content = """# RunPod Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. GitHub Actions Permission Errors

**Issue**: `Error: denied: installation not allowed to Write organization package`

**Solutions**:
- Ensure the repository has package write permissions
- Check if the organization allows package creation
- Verify the GITHUB_TOKEN has the correct scopes

**Steps to fix**:
1. Go to repository Settings > Actions > General
2. Ensure "Read and write permissions" is selected
3. Check organization settings for package permissions

### 2. Docker Image Build Failures

**Issue**: Docker build fails or image is not pushed

**Solutions**:
- Check the workflow logs for specific errors
- Verify Dockerfile syntax
- Ensure all required files are present

### 3. RunPod Environment Variables

**Required Environment Variables for RunPod**:
```bash
RUNPOD_POD_ID=<your-pod-id>
RUNPOD_TCP_PORT_8000=8000
OLLAMA_BASE_URL=http://localhost:11434
MODEL_CACHE_DIR=/app/cache
LOG_LEVEL=INFO
```

### 4. Model Initialization Issues

**Issue**: Models not loading or API returning empty responses

**Solutions**:
1. Run the validation script:
   ```bash
   python scripts/validate_startup.py
   ```

2. Check model discovery:
   ```bash
   python scripts/debug-model-discovery.py
   ```

3. Run the comprehensive fix:
   ```bash
   python scripts/comprehensive-production-fix.py
   ```

### 5. API Testing

**Test the chat endpoint**:
```bash
curl -X POST http://localhost:8000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"message": "Test message", "stream": false}'
```

**Expected Response**:
```json
{
  "response": "AI generated response",
  "status": "success",
  "model_used": "llama3.2:latest"
}
```

### 6. Container Logs and Debugging

**View container logs**:
```bash
docker logs ai-search-system
```

**Enter container for debugging**:
```bash
docker exec -it ai-search-system bash
```

**Check service status inside container**:
```bash
supervisorctl status
```

### 7. Health Checks

**Application health endpoint**:
```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Deployment Checklist

- [ ] GitHub Actions workflow completed successfully
- [ ] Docker image pushed to registry
- [ ] RunPod environment variables set
- [ ] Container started successfully
- [ ] Health checks passing
- [ ] Models loading correctly
- [ ] Chat API responding
- [ ] End-to-end test completed

## Contact and Support

If issues persist:
1. Check the GitHub Actions logs
2. Review container logs
3. Run the troubleshooting scripts
4. Verify all environment variables are set correctly
"""

        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
            
        print(f"✅ Troubleshooting guide created: {guide_path}")
    
    def run_full_diagnostic(self) -> None:
        """Run a comprehensive diagnostic of the deployment pipeline"""
        print("🚀 Running RunPod Deployment Diagnostic")
        print("=" * 50)
        
        # Check GitHub Actions
        workflow_status = self.check_github_actions_status()
        print()
        
        # Check container registry
        registry_ok = self.check_container_registry_permissions()
        print()
        
        # Check repository settings
        repo_settings = self.check_repository_settings()
        print()
        
        # Check Docker image
        image_ok = self.check_docker_image_availability()
        print()
        
        # Generate deployment commands
        commands = self.generate_runpod_deployment_commands()
        
        print("📋 RunPod Deployment Commands:")
        print("-" * 30)
        for cmd in commands:
            print(cmd)
        print()
        
        # Create troubleshooting guide
        self.create_runpod_troubleshooting_guide()
        print()
        
        # Summary
        print("📊 Diagnostic Summary:")
        print(f"   GitHub Actions: {'✅' if workflow_status.get('conclusion') == 'success' else '⚠️'}")
        print(f"   Registry Access: {'✅' if registry_ok else '❌'}")
        print(f"   Repository: {'✅' if repo_settings.get('accessible') else '❌'}")
        print(f"   Docker Image: {'✅' if image_ok else '❌'}")
        
        print("\n🎯 Next Steps:")
        if not workflow_status.get('conclusion') == 'success':
            print("   1. Check GitHub Actions workflow logs")
            print("   2. Fix any build errors")
            print("   3. Push fixes and wait for successful build")
        
        if not image_ok:
            print("   4. Wait for Docker image to be built and pushed")
            print("   5. Authenticate with container registry if needed")
        
        print("   6. Deploy on RunPod using the generated commands")
        print("   7. Set the required environment variables")
        print("   8. Test the API endpoints")
        print("   9. Run final validation scripts")

def main():
    """Main function"""
    repo_path = os.getcwd()
    
    troubleshooter = RunPodDeploymentTroubleshooter(repo_path)
    troubleshooter.run_full_diagnostic()

if __name__ == "__main__":
    main()
