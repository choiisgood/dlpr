#!/bin/bash
# yt-dlp Web App — 자동 설치 스크립트
# 사용법: bash install.sh
set -e

echo ""
echo "======================================"
echo "  yt-dlp Web App 설치 시작"
echo "======================================"
echo ""

# ─── 1. 시스템 패키지 ───────────────────────────────────────────────
echo "[1/5] 시스템 패키지 업데이트..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip ffmpeg curl

# ─── 2. Python 패키지 ───────────────────────────────────────────────
echo "[2/5] Python 패키지 설치..."
pip3 install --upgrade yt-dlp flask flask-cors

# ─── 3. 다운로드 디렉토리 ────────────────────────────────────────────
echo "[3/5] 다운로드 폴더 생성..."
mkdir -p ~/downloads
echo "    → ~/downloads 생성됨"

# ─── 4. 시크릿 키 설정 ───────────────────────────────────────────────
echo ""
echo "[4/5] 시크릿 키 설정"
read -p "  사용할 비밀번호 입력 (엔터 = 기본값 changeme123): " USER_KEY
if [ -z "$USER_KEY" ]; then
  USER_KEY="changeme123"
  echo "  ⚠️  기본값(changeme123)을 사용합니다. 나중에 꼭 바꾸세요!"
fi

# 환경변수를 .bashrc에 저장
echo "export YTDLP_SECRET=\"$USER_KEY\"" >> ~/.bashrc
export YTDLP_SECRET="$USER_KEY"
echo "  ✅ 시크릿 키 저장됨"

# ─── 5. systemd 서비스 등록 ──────────────────────────────────────────
echo ""
echo "[5/5] systemd 서비스 등록..."

WORK_DIR="$(pwd)"
USER_NAME="$(whoami)"

sudo tee /etc/systemd/system/ytdlp-webapp.service > /dev/null <<EOF
[Unit]
Description=yt-dlp Web App
After=network.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${WORK_DIR}
Environment=YTDLP_SECRET=${USER_KEY}
ExecStart=/usr/bin/python3 ${WORK_DIR}/server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ytdlp-webapp
sudo systemctl start ytdlp-webapp

echo ""
echo "======================================"
echo "  ✅ 설치 완료!"
echo "======================================"
echo ""
echo "  접속 주소 : http://$(hostname -I | awk '{print $1}'):8080"
echo "  시크릿 키 : $USER_KEY"
echo "  저장 경로 : ~/downloads"
echo ""
echo "  서비스 상태 확인: sudo systemctl status ytdlp-webapp"
echo "  로그 확인       : sudo journalctl -u ytdlp-webapp -f"
echo ""
