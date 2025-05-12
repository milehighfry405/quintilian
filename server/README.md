# Quintilian Server

This is the server component of the Quintilian voice assistant. It provides an API endpoint for processing audio input and returning both text and audio responses.

## Setup

1. Create an EC2 key pair:
   ```bash
   aws ec2 create-key-pair --key-name quintilian-key --query 'KeyMaterial' --output text > quintilian-key.pem
   chmod 400 quintilian-key.pem
   ```

2. Set up your environment variables:
   ```bash
   export OPENAI_API_KEY=your_openai_key
   export ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

3. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Server

### Local Development
```bash
uvicorn main:app --reload
```

### Production (EC2)
```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

## API Endpoints

### POST /process-audio
Process audio input and return both text and audio responses.

**Request:**
- Content-Type: multipart/form-data
- Body: audio file (WAV format)

**Response:**
```json
{
    "text": "Response text from GPT-4",
    "audio_url": "URL to the generated audio response"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy"
}
```

## Deployment

To deploy to EC2:
1. Make sure you have AWS credentials configured
2. Run the deployment script:
   ```bash
   python deploy_ec2.py
   ```
3. The script will create an EC2 instance and print the connection details

## Security Notes

- The server is configured to accept connections from any origin (CORS). In production, you should restrict this to your specific domains.
- The EC2 security group allows inbound traffic on port 8000. Consider restricting this to specific IP ranges in production.
- API keys are stored in environment variables. Make sure to keep these secure and never commit them to version control. 