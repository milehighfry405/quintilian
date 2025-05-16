import os
import subprocess
import time
import requests
from pathlib import Path

# Configuration
SERVER_IP = "13.57.89.95"
KEY_PATH = "../q key.pem"
REMOTE_USER = "ubuntu"
REMOTE_DIR = "/home/ubuntu/server"
LOCAL_MAIN = "main.py"
REMOTE_MAIN = f"{REMOTE_DIR}/main.py"
SERVICE_NAME = "quintilian"  # Change if your systemd service is named differently
HEALTH_URL = f"http://{SERVER_IP}:8000/health"


def run_ssh_command(command):
    ssh_cmd = [
        "ssh", "-i", KEY_PATH, f"{REMOTE_USER}@{SERVER_IP}", command
    ]
    print(f"Running SSH command: {command}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode == 0


def scp_file(local_path, remote_path):
    scp_cmd = [
        "scp", "-i", KEY_PATH, local_path, f"{REMOTE_USER}@{SERVER_IP}:{remote_path}"
    ]
    print(f"Copying {local_path} to {remote_path} on server...")
    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode == 0


def check_server_health():
    print(f"Checking server health at {HEALTH_URL} ...")
    try:
        resp = requests.get(HEALTH_URL, timeout=3)
        print(f"Status code: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def main():
    # Check key file
    if not Path(KEY_PATH).exists():
        print(f"Key file {KEY_PATH} not found!")
        return
    # Check local main.py
    if not Path(LOCAL_MAIN).exists():
        print(f"Local {LOCAL_MAIN} not found!")
        return
    # Copy main.py
    if not scp_file(LOCAL_MAIN, REMOTE_MAIN):
        print("SCP failed. Aborting.")
        return
    print("main.py copied successfully.")
    # Restart the service
    print(f"Restarting service {SERVICE_NAME} ...")
    if not run_ssh_command(f"sudo systemctl restart {SERVICE_NAME}"):
        print("Failed to restart service. Aborting.")
        return
    print("Service restarted. Waiting for server to come up...")
    # Wait and check health
    for i in range(10):
        time.sleep(3)
        if check_server_health():
            print("Server is healthy and running the new main.py!")
            return
        else:
            print(f"Health check {i+1}/10 failed, retrying...")
    print("Server did not become healthy in time. Please check logs.")

if __name__ == "__main__":
    main() 