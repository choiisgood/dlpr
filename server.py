#!/usr/bin/env python3
"""
yt-dlp Web App - Backend Server
Requirements: pip3 install flask yt-dlp flask-cors
Usage: python3 server.py
"""

import os
import json
import uuid
import threading
import subprocess
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

# ─── 설정 ───────────────────────────────────────────────────────────────────
ALLOWED_DIRS = {
    "komq":   "/media/paradise/komq",
    "milkoy": "/media/paradise/milkoy",
}
SECRET_KEY   = os.environ.get("YTDLP_SECRET", "changeme123")   # 환경변수로 덮어쓰기 권장
MAX_JOBS     = 5          # 동시 최대 작업 수
# ────────────────────────────────────────────────────────────────────────────

# 작업 상태 저장 (메모리 내 — 서버 재시작 시 초기화됨)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


def run_download(job_id: str, url: str, quality: str, audio_only: bool, dest: str):
    """백그라운드 스레드에서 yt-dlp 실행"""
    with jobs_lock:
        jobs[job_id]["status"] = "downloading"
        jobs[job_id]["started_at"] = datetime.now().isoformat()

    os.makedirs(dest, exist_ok=True)

    cmd = ["yt-dlp", "--no-playlist"]

    if audio_only:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        if quality == "best":
            cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
        elif quality == "1080":
            cmd += ["-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"]
        elif quality == "720":
            cmd += ["-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"]
        elif quality == "480":
            cmd += ["-f", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"]
        else:
            cmd += ["-f", "best"]

    output_tmpl = os.path.join(dest, "%(title).80s.%(ext)s")
    cmd += [
        "-o", output_tmpl,
        "--merge-output-format", "mp4",
        "--embed-thumbnail",
        "--add-metadata",
        "--progress",
        url
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        log_lines = []
        for line in proc.stdout:
            line = line.strip()
            if line:
                log_lines.append(line)
                # 진행률 파싱 (예: [download]  45.3% of 123.45MiB)
                if "[download]" in line and "%" in line:
                    try:
                        pct_str = line.split("%")[0].split()[-1]
                        pct = float(pct_str)
                        with jobs_lock:
                            jobs[job_id]["progress"] = pct
                            jobs[job_id]["log"] = line
                    except (ValueError, IndexError):
                        pass
                with jobs_lock:
                    jobs[job_id]["log"] = line

        proc.wait()

        with jobs_lock:
            if proc.returncode == 0:
                jobs[job_id]["status"]     = "done"
                jobs[job_id]["progress"]   = 100
                jobs[job_id]["log"]        = "✅ 다운로드 완료"
            else:
                jobs[job_id]["status"]     = "error"
                jobs[job_id]["log"]        = "\n".join(log_lines[-5:]) or "알 수 없는 오류"
            jobs[job_id]["finished_at"] = datetime.now().isoformat()

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"]     = "error"
            jobs[job_id]["log"]        = str(e)
            jobs[job_id]["finished_at"] = datetime.now().isoformat()


# ─── API 엔드포인트 ──────────────────────────────────────────────────────────

@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json(silent=True) or {}

    # 인증
    if data.get("key") != SECRET_KEY:
        return jsonify({"error": "인증 실패 — 올바른 시크릿 키를 입력하세요."}), 403

    url = (data.get("url") or "").strip()
    if not url.startswith("http"):
        return jsonify({"error": "올바른 URL을 입력하세요."}), 400

    # 동시 작업 수 제한
    with jobs_lock:
        active = sum(1 for j in jobs.values() if j["status"] in ("queued", "downloading"))
    if active >= MAX_JOBS:
        return jsonify({"error": f"최대 동시 작업 수({MAX_JOBS})를 초과했습니다. 잠시 후 시도하세요."}), 429

    quality    = data.get("quality", "best")
    audio_only = bool(data.get("audio_only", False))
    dest_key   = data.get("dest", "")
    job_id     = str(uuid.uuid4())[:8]

    # 프리셋 경로 또는 커스텀 경로 처리
    if dest_key in ALLOWED_DIRS:
        dest = ALLOWED_DIRS[dest_key]
    elif dest_key.startswith('/'):
        # 커스텀 절대 경로 — 기본 보안 검사
        dest = os.path.normpath(dest_key)
        if dest in ('/', '/etc', '/bin', '/usr', '/sys', '/proc'):
            return jsonify({"error": "허용되지 않는 경로입니다."}), 400
    else:
        return jsonify({"error": "올바른 저장 경로를 입력하세요."}), 400

    with jobs_lock:
        jobs[job_id] = {
            "id":          job_id,
            "url":         url,
            "quality":     "MP3" if audio_only else quality,
            "dest":        dest,
            "status":      "queued",
            "progress":    0,
            "log":         "대기 중...",
            "created_at":  datetime.now().isoformat(),
            "started_at":  None,
            "finished_at": None,
        }

    t = threading.Thread(target=run_download, args=(job_id, url, quality, audio_only, dest), daemon=True)
    t.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/status/<job_id>")
def job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "작업을 찾을 수 없습니다."}), 404
    return jsonify(job)


@app.route("/api/jobs")
def list_jobs():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        return jsonify({"error": "인증 실패"}), 403
    with jobs_lock:
        return jsonify(list(reversed(list(jobs.values()))))


@app.route("/api/clear", methods=["POST"])
def clear_jobs():
    data = request.get_json(silent=True) or {}
    if data.get("key") != SECRET_KEY:
        return jsonify({"error": "인증 실패"}), 403
    with jobs_lock:
        # 완료/오류 작업만 제거
        to_del = [jid for jid, j in jobs.items() if j["status"] in ("done", "error")]
        for jid in to_del:
            del jobs[jid]
    return jsonify({"cleared": len(to_del)})


# ─── 프론트엔드 서빙 ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ─── 실행 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dirs = ", ".join(ALLOWED_DIRS.values())
    print("=" * 44)
    print("  yt-dlp Web App 시작")
    print("=" * 44)
    print(f"  URL       : http://0.0.0.0:8080")
    print(f"  저장 경로 : {dirs}")
    print(f"  시크릿 키 : {SECRET_KEY}")
    print("=" * 44)
    print()
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
