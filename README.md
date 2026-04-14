# DLPR — yt-dlp Web App

> 휴대폰에서 링크를 붙여넣으면 우분투 서버에 자동으로 영상이 다운로드되는 셀프호스티드 웹 앱

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=flat-square&logo=youtube&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)


---

## 주요 기능

- **링크 붙여넣기 → 즉시 다운로드** — YouTube, Instagram, TikTok, Twitter, Chzzk 등 yt-dlp 지원 사이트 전부 동작
- **화질 선택** — BEST / 1080p / 720p / 480p
- **Audio Only** — MP3 추출
- **저장 경로 선택** — 직접 입력 지원
- **실시간 진행률** — 다운로드 퍼센트 & 로그 1.5초마다 자동 갱신
- **시크릿 키 인증** — 본인만 사용 가능한 간단한 인증
- **클립보드 자동 붙여넣기** — URL 입력창 클릭 시 클립보드 내용 자동 채움

---

## 구조

```
dlpr/
├── server.py      # Flask 백엔드 (API + yt-dlp 실행)
├── index.html     # 프론트엔드 웹 UI
└── install.sh     # 자동 설치 스크립트
```

---

## 설치

### 요구사항

- Ubuntu 20.04+
- Python 3.10+
- ffmpeg

### 자동 설치 (권장)

```bash
git clone https://github.com/yourname/dlpr.git
cd dlpr
chmod +x install.sh
bash install.sh
```

설치 스크립트가 아래를 자동으로 처리합니다.

1. `python3`, `ffmpeg`, `pip3` 설치
2. `yt-dlp`, `flask`, `flask-cors`, `gunicorn` 설치
3. 시크릿 키 설정 (입력 프롬프트)
4. systemd 서비스 등록 및 자동 시작

### 수동 설치

```bash
# 패키지 설치
sudo apt update && sudo apt install -y python3 python3-pip ffmpeg

pip3 install yt-dlp flask flask-cors gunicorn

# 시크릿 키 설정
export YTDLP_SECRET="your_password_here"

# 서버 실행
cd dlpr
gunicorn -w 2 -b 0.0.0.0:8080 server:app
```

---

## 설정

`server.py` 상단의 설정 값을 수정하세요.

```python
ALLOWED_DIRS = {
    "komq":   "/media/paradise/komq",    # 프리셋 경로 1
    "milkoy": "/media/paradise/milkoy",  # 프리셋 경로 2
}
MAX_JOBS = 5  # 최대 동시 다운로드 수
```

시크릿 키는 환경변수로 관리하는 것을 권장합니다.

```bash
export YTDLP_SECRET="my_strong_password"
```

---


## API

| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `GET /` | GET | 웹 UI 서빙 |
| `/api/download` | POST | 다운로드 시작 |
| `/api/status/:id` | GET | 작업 상태 조회 |
| `/api/jobs` | GET | 전체 작업 목록 |
| `/api/clear` | POST | 완료/오류 작업 삭제 |

**다운로드 요청 예시**

```json
POST /api/download
{
  "key": "your_secret",
  "url": "https://youtube.com/watch?v=xxxxx",
  "quality": "720",
  "audio_only": false,
  "dest": "komq"
}
```

`dest` 값은 `komq`, `milkoy`, 또는 `/media/...` 형태의 절대 경로.

---

## 서비스 관리

```bash
# 상태 확인
sudo systemctl status ytdlp-webapp

# 재시작
sudo systemctl restart ytdlp-webapp

# 로그 실시간 확인
sudo journalctl -u ytdlp-webapp -f

# 중지
sudo systemctl stop ytdlp-webapp
```

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3, Flask, Gunicorn |
| 다운로더 | yt-dlp, ffmpeg |
| 프론트엔드 | Vanilla HTML/CSS/JS |
| 폰트 | Space Mono, Sora (Google Fonts) |
| 프로세스 관리 | systemd |

---

## 라이선스

MIT
