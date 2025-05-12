import boto3
import time
import os
import shutil
from pathlib import Path
import paramiko
import sys

def create_key_pair(ec2_client, key_name):
    """Create a new key pair for EC2 instance."""
    try:
        # Delete existing key pair if it exists
        try:
            ec2_client.delete_key_pair(KeyName=key_name)
            print(f"Deleted existing key pair: {key_name}")
        except:
            pass

        # Create new key pair
        key_pair = ec2_client.create_key_pair(KeyName=key_name)
        
        # Save the private key to a file in the user's home directory
        key_path = os.path.join(os.path.expanduser("~"), f"{key_name}.pem")
        with open(key_path, "w") as f:
            f.write(key_pair["KeyMaterial"])
        
        # Set proper permissions for the key file
        if sys.platform != "win32":
            os.chmod(key_path, 0o400)
        else:
            # On Windows, we'll just print a warning
            print("WARNING: On Windows, you may need to manually set key file permissions")
            print("Right-click the .pem file -> Properties -> Security -> Advanced -> Disable inheritance")
            print("Then remove all permissions except your user")
        
        print(f"Created key pair: {key_name}")
        print(f"Key file saved to: {key_path}")
        return True
    except Exception as e:
        print(f"Error creating key pair: {e}")
        return False

def create_security_group(ec2_client, group_name):
    """Create a security group for the EC2 instance."""
    try:
        # Create security group
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description="Security group for Quintilian server"
        )
        security_group_id = response["GroupId"]
        
        # Allow SSH access
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
            ]
        )
        
        # Allow HTTP access for FastAPI
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
            ]
        )
        
        print(f"Created security group: {group_name}")
        return security_group_id
    except ec2_client.exceptions.ClientError as e:
        if "InvalidGroup.Duplicate" in str(e):
            print(f"Security group {group_name} already exists")
            # Get the existing security group ID
            response = ec2_client.describe_security_groups(GroupNames=[group_name])
            return response["SecurityGroups"][0]["GroupId"]
        print(f"Error creating security group: {e}")
        return None

def create_ec2_instance(ec2_client, security_group_id, key_name):
    """Create an EC2 instance."""
    try:
        # Create EC2 instance
        response = ec2_client.run_instances(
            ImageId="ami-0f8e81a3da6e2510a",  # Ubuntu 22.04 LTS in us-west-1
            InstanceType="t2.micro",
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            UserData="""#!/bin/bash
apt-get update
apt-get install -y python3-pip python3-venv
cd /home/ubuntu
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install uvicorn fastapi
""",
            TagSpecifications=[
                {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "Quintilian-Server"}]}
            ]
        )
        
        instance_id = response["Instances"][0]["InstanceId"]
        print(f"Created EC2 instance: {instance_id}")
        
        # Wait for instance to be running
        waiter = ec2_client.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        
        # Get the public IP address
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = response["Reservations"][0]["Instances"][0]["PublicIpAddress"]
        print(f"Instance public IP: {public_ip}")
        
        return instance_id, public_ip
    except Exception as e:
        print(f"Error creating EC2 instance: {e}")
        return None, None

def deploy_server(public_ip, key_name):
    """Deploy the server code to EC2 instance."""
    try:
        deploy_dir = Path("deploy_temp")
        if deploy_dir.exists():
            print("Cleaning up existing deploy_temp directory...")
            shutil.rmtree(deploy_dir)
        deploy_dir.mkdir()
        
        # Copy current directory contents
        for item in os.listdir("."):
            if item not in ["deploy_temp", "deploy_ec2.py", "quintilian-key.pem"]:
                if os.path.isdir(item):
                    shutil.copytree(item, deploy_dir / item)
                else:
                    shutil.copy(item, deploy_dir / item)
        
        # Create systemd service file
        service_content = """[Unit]
Description=Quintilian Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/quintilian
Environment=\"PATH=/home/ubuntu/venv/bin\"
ExecStart=/home/ubuntu/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
"""
        with open(deploy_dir / "quintilian.service", "w", newline='\n') as f:
            f.write(service_content)
        
        # Create deployment script
        deploy_script = """#!/bin/bash
cd /home/ubuntu
mkdir -p quintilian
cp -r /tmp/deploy/* quintilian/
cd quintilian
source /home/ubuntu/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
sudo cp quintilian.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable quintilian
sudo systemctl restart quintilian
sleep 5
sudo systemctl status quintilian
"""
        with open(deploy_dir / "deploy.sh", "w", newline='\n') as f:
            f.write(deploy_script)
        os.chmod(deploy_dir / "deploy.sh", 0o755)
        
        # Create .env file
        env_content = f"""OPENAI_API_KEY={os.getenv('OPENAI_API_KEY')}
ELEVENLABS_API_KEY={os.getenv('ELEVENLABS_API_KEY')}
"""
        with open(deploy_dir / ".env", "w") as f:
            f.write(env_content)
        
        # SFTP upload
        key = paramiko.RSAKey.from_private_key_file(f"{key_name}.pem")
        transport = paramiko.Transport((public_ip, 22))
        transport.connect(username="ubuntu", pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)
        # Recursively upload deploy_dir to /tmp/deploy on remote
        def upload_dir(local, remote):
            for item in os.listdir(local):
                local_path = os.path.join(local, item)
                remote_path = remote + "/" + item
                if os.path.isdir(local_path):
                    try:
                        sftp.mkdir(remote_path)
                    except:
                        pass
                    upload_dir(local_path, remote_path)
                else:
                    sftp.put(local_path, remote_path)
        try:
            sftp.mkdir("/tmp/deploy")
        except:
            pass
        upload_dir(str(deploy_dir), "/tmp/deploy")
        sftp.close()
        transport.close()
        
        # SSH and run deploy.sh
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username="ubuntu", key_filename=f"{key_name}.pem")
        stdin, stdout, stderr = ssh.exec_command("bash /tmp/deploy/deploy.sh")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Check server status
        print("\nChecking server status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status quintilian")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Check if port 8000 is listening
        stdin, stdout, stderr = ssh.exec_command("sudo netstat -tulpn | grep 8000")
        print("\nChecking if port 8000 is listening:")
        print(stdout.read().decode())
        
        ssh.close()
        
        print("Server deployed successfully!")
        print(f"Server URL: http://{public_ip}:8000")
        
        # Clean up
        try:
            print("Contents of deploy_temp before deletion:")
            for item in os.listdir(deploy_dir):
                print(f"  {item}")
            shutil.rmtree(deploy_dir)
        except Exception as e:
            print(f"Warning: Could not delete deploy_temp: {e}")
        
    except Exception as e:
        print(f"Error deploying server: {e}")

def main():
    # Initialize AWS clients
    ec2_client = boto3.client("ec2")
    
    # Configuration
    key_name = "quintilian-key"
    security_group_name = "quintilian-sg"
    
    # Create key pair
    if not create_key_pair(ec2_client, key_name):
        return
    
    # Create security group
    security_group_id = create_security_group(ec2_client, security_group_name)
    if not security_group_id:
        return
    
    # Create EC2 instance
    instance_id, public_ip = create_ec2_instance(ec2_client, security_group_id, key_name)
    if not instance_id or not public_ip:
        return
    
    print("\nInstance created successfully!")
    print(f"Public IP: {public_ip}")
    print(f"Key file: {key_name}.pem")
    print("\nTo SSH into the instance:")
    print(f"ssh -i {key_name}.pem ubuntu@{public_ip}")

if __name__ == "__main__":
    main() 