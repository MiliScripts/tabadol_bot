#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# =========================
# CONFIGURATION
# =========================

BID_DIR = "/root/bid"

SERVICES = {
    "update_handler": {
        "description": "Bid Scrapper Update Handler",
        "script": "scrapper/update_handler.py",
        "working_dir": "scrapper"
    },

    "bid_backuper": {
        "description": "BID Backuper Service",
        "script": "backuper.py",
        "working_dir": ""
    },

    "bid_transactions_report": {
        "description": "BID Transactions Daily Report Service",
        "script": "transactions_daily_report.py",
        "working_dir": ""
    },

    "bid_bot": {
        "description": "BID Telegram Bot Service",
        "script": "main.py",
        "working_dir": ""
    },

    # =========================
    # PARACHI SERVICES
    # =========================

    "parachi-price-story-image": {
        "description": "parachi-price-story-image Service",
        "script": "parachi_price_story_image/app.py",
        "working_dir": "parachi_price_story_image"
    },

    "parachi-auth-bot": {
        "description": "parachi-auth-bot Service",
        "script": "parachi_auth_bot.py",
        "working_dir": ""
    },

    "parachi-price-updates": {
        "description": "parachi-price-updates Service",
        "script": "parachi_price_updates.py",
        "working_dir": ""
    }
}

# =========================
# HELPERS
# =========================

def run_command(cmd, cwd=None, exit_on_error=True):
    print(f"\n>>> Running: {cmd}")

    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()

    if stdout:
        print(stdout)

    if process.returncode != 0:
        print(f"ERROR: {cmd}")

        if stderr:
            print(stderr)

        if exit_on_error:
            sys.exit(1)

        return None

    return stdout


def service_exists(service_name):
    result = subprocess.run(
        ["systemctl", "list-unit-files", f"{service_name}.service"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return service_name in result.stdout


def service_is_running(service_name):
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", service_name]
    )

    return result.returncode == 0


# =========================
# VENV
# =========================

def create_venv():
    venv_path = os.path.join(BID_DIR, "venv")

    if os.path.exists(venv_path):
        print("✓ venv already exists")
        return

    print("Creating virtual environment...")
    run_command(f"python3 -m venv {venv_path}")


def install_requirements():
    req_file = os.path.join(BID_DIR, "requirements.txt")

    if not os.path.exists(req_file):
        print("No requirements.txt found")
        return

    pip = os.path.join(BID_DIR, "venv", "bin", "pip")

    print("Installing requirements...")
    run_command(f"{pip} install -r {req_file}")


# =========================
# SERVICE CREATION
# =========================

def create_service(name, config):
    service_path = f"/etc/systemd/system/{name}.service"

    service_content = f"""[Unit]
Description={config['description']}
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={os.path.join(BID_DIR, config['working_dir'])}
ExecStart={os.path.join(BID_DIR, 'venv', 'bin', 'python')} {os.path.join(BID_DIR, config['script'])}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier={name}

[Install]
WantedBy=multi-user.target
"""

    # Write/update service file
    with open(service_path, "w") as f:
        f.write(service_content)

    print(f"✓ Service file updated: {name}")

    # Reload systemd
    run_command("systemctl daemon-reload")

    # Enable service
    run_command(f"systemctl enable {name}", exit_on_error=False)

    # Skip restart if already running
    if service_is_running(name):
        print(f"✓ {name} already running -> skipping restart")
    else:
        print(f"Starting {name}...")
        run_command(f"systemctl start {name}")

    print(f"✓ Service ready: {name}")


# =========================
# BID BOT AUTO RESTART
# =========================

def create_bid_bot_restart_service():
    service_name = "bid-bot-auto-restart"

    service_path = f"/etc/systemd/system/{service_name}.service"
    timer_path = f"/etc/systemd/system/{service_name}.timer"

    # SERVICE
    service_content = """[Unit]
Description=Restart bid_bot every 10 minutes

[Service]
Type=oneshot
ExecStart=/bin/systemctl restart bid_bot
"""

    # TIMER
    timer_content = """[Unit]
Description=Run bid-bot-auto-restart every 10 minutes

[Timer]
OnBootSec=10min
OnUnitActiveSec=10min
Unit=bid-bot-auto-restart.service

[Install]
WantedBy=timers.target
"""

    with open(service_path, "w") as f:
        f.write(service_content)

    with open(timer_path, "w") as f:
        f.write(timer_content)

    print("✓ bid-bot-auto-restart timer/service created")

    run_command("systemctl daemon-reload")

    run_command(
        f"systemctl enable {service_name}.timer",
        exit_on_error=False
    )

    if service_is_running(f"{service_name}.timer"):
        print("✓ bid-bot-auto-restart timer already running")
    else:
        run_command(f"systemctl start {service_name}.timer")

    print("✓ bid_bot auto restart every 10 minutes enabled")


# =========================
# MAIN
# =========================

def main():
    if os.geteuid() != 0:
        print("Please run as root")
        sys.exit(1)

    Path(BID_DIR).mkdir(parents=True, exist_ok=True)

    create_venv()

    install_requirements()

    print("\n=========================")
    print("DEPLOYING SERVICES")
    print("=========================\n")

    for name, cfg in SERVICES.items():
        create_service(name, cfg)

    print("\n=========================")
    print("SETTING UP AUTO RESTART")
    print("=========================\n")

    create_bid_bot_restart_service()

    print("\n=========================")
    print("ALL SERVICES READY")
    print("=========================\n")

    run_command(
        "systemctl list-units --type=service | grep -E 'bid|parachi'",
        exit_on_error=False
    )

    print("\n=========================")
    print("ACTIVE TIMERS")
    print("=========================\n")

    run_command(
        "systemctl list-timers | grep bid-bot-auto-restart",
        exit_on_error=False
    )


if __name__ == "__main__":
    main()