import os

def setup_cicd():
    print("🚀 Setting up CI/CD pipeline for tabadol_bot...")

    # 1. Create .github/workflows directory
    workflow_dir = os.path.join(".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    file_path = os.path.join(workflow_dir, "deploy.yml")

    # 2. CI/CD workflow YAML configuration
    yaml_content = """name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  # --- CI: BUILD & CACHE ---
  build:
    name: Build & Cache
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Verify Requirements
        run: pip install -r requirements.txt

  # --- CD: AUTO DEPLOY TO VPS ---
  deploy:
    name: Deploy to Server
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: SSH and Update Server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_IP }}
          username: root
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            echo "🚀 Deploying updates to /root/bid..."
            cd /root/bid
            
            # Safe pull (keeps databases and sessions untouched)
            git reset --hard HEAD
            git pull origin main
            
            # Update Python environment
            source venv/bin/activate
            pip install -r requirements.txt
            
            # Restart bot services
            echo "🔄 Restarting bot..."
            bash restart.sh
            
            echo "✅ Deployment Finished Successfully!"
"""

    # 3. Write deploy.yml
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"✅ Generated: {file_path}")
    print("\n" + "=" * 60)
    print("🎉 All set! Now push this to GitHub to activate the pipeline:")
    print("   git add .")
    print('   git commit -m "Configure CI/CD auto-deploy with caching"')
    print("   git push origin main")
    print("=" * 60)

if __name__ == "__main__":
    setup_cicd()