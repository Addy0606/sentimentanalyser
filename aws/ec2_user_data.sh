#!/bin/bash
# EC2 User Data Bootstrap for Stock Sentiment Analyser
set -e

# Update and install dependencies
dnf update -y
dnf install -y python3.12 python3.12-pip git

# Create application directory
mkdir -p /opt/stock-sentiment
cd /opt/stock-sentiment

# Setup Python Virtual Environment
python3.12 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install streamlit pandas sqlalchemy psycopg2-binary vaderSentiment requests boto3 python-dotenv

# Create systemd service for Streamlit
cat << 'EOF' > /etc/systemd/system/stock-sentiment.service
[Unit]
Description=Stock Sentiment Analyser Streamlit Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/opt/stock-sentiment
Environment="PATH=/opt/stock-sentiment/venv/bin:/usr/bin"
Environment="AWS_DEFAULT_REGION=ap-south-1"
ExecStart=/opt/stock-sentiment/venv/bin/streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable stock-sentiment.service
echo "Stock Sentiment Analyser bootstrap completed successfully."
