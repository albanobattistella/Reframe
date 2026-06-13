import asyncio
import os
import re
import uuid
import subprocess
from fastapi import FastAPI, UploadFile, Form, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional

app = FastAPI(title="Reframe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
UPLOAD_DIR = "/app/uploads" if os.environ.get("DOCKER") else os.path.join(os.getcwd(), "uploads")
EXPORT_DIR = "/app/exports" if os.environ.get("DOCKER") else os.path.join(os.getcwd(), "exports")
FRONTEND_DIR = "/app/frontend" if os.environ.get("DOCKER") else os.path.join(os.path.dirname(os.getcwd()), "frontend", "dist")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# State stores
job_progress: Dict[str, int] = {}
job_status: Dict[str, str] = {}
active_connections: Dict[str, list[WebSocket]] = {}

def get_video_duration(filepath: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0

async def process_video_ffmpeg(
    job_id: str, 
    input_path: str, 
    output_path: str, 
    x: int, y: int, w: int, h: int, 
    quality: str, 
    muteAudio: str,
    trimStart: float = None,
    trimEnd: float = None,
    logo_paths: List[str] = None,
    logoXs: List[int] = None,
    logoYs: List[int] = None,
    logoWs: List[int] = None,
    logoHs: List[int] = None,
    logoRotations: List[float] = None,
    logoOpacities: List[int] = None,
    text_paths: List[str] = None,
    textXs: List[int] = None,
    textYs: List[int] = None,
    textWs: List[int] = None,
    textHs: List[int] = None,
    textRotations: List[float] = None
):
    logo_paths = logo_paths or []
    logoXs = logoXs or []
    logoYs = logoYs or []
    logoWs = logoWs or []
    logoHs = logoHs or []
    logoRotations = logoRotations or []
    logoOpacities = logoOpacities or []
    
    text_paths = text_paths or []
    textXs = textXs or []
    textYs = textYs or []
    textWs = textWs or []
    textHs = textHs or []
    textRotations = textRotations or []
    duration = get_video_duration(input_path)
    if trimStart is not None and trimEnd is not None:
        duration = trimEnd - trimStart
        
    job_status[job_id] = "processing"
    job_progress[job_id] = 0
    
    # Quality settings
    crf = "18" if quality == "high" else "23"
    preset = "slow" if quality == "high" else "fast"
    
    cmd = ["ffmpeg", "-y"]
    
    if trimStart is not None and trimStart > 0:
        cmd.extend(["-ss", str(trimStart)])
    if trimEnd is not None and trimEnd > 0:
        cmd.extend(["-to", str(trimEnd)])
        
    cmd.extend(["-i", input_path])
    
    filters = [f"[0:v]crop={w}:{h}:{x}:{y}[bg]"]
    current_bg = "[bg]"
    input_idx = 1
    
    for i, logo_path in enumerate(logo_paths):
        cmd.extend(["-i", logo_path])
        rotation = logoRotations[i] if i < len(logoRotations) and logoRotations[i] is not None else 0
        rotation_expr = f"{rotation}*PI/180"
        
        opacity = logoOpacities[i] if i < len(logoOpacities) and logoOpacities[i] is not None else 100
        opacity_val = opacity / 100.0
        opacity_filter = f",format=rgba,colorchannelmixer=aa={opacity_val}" if opacity_val < 1.0 else ""
        
        lW = logoWs[i] if i < len(logoWs) else 150
        lH = logoHs[i] if i < len(logoHs) else None
        lX = logoXs[i] if i < len(logoXs) else 0
        lY = logoYs[i] if i < len(logoYs) else 0
        
        if lH is not None:
            rotate_filter = f"rotate={rotation_expr}:c=none:ow='hypot(iw,ih)':oh='hypot(iw,ih)'"
            overlay_expr = f"{lX}+{lW}/2-w/2:{lY}+{lH}/2-h/2"
        else:
            rotate_filter = f"rotate={rotation_expr}:c=none"
            overlay_expr = f"{lX}:{lY}"
            
        filters.append(f"[{input_idx}:v]scale={lW}:-1{opacity_filter}[l_scaled_{i}]")
        filters.append(f"[l_scaled_{i}]{rotate_filter}[l_rotated_{i}]")
        filters.append(f"{current_bg}[l_rotated_{i}]overlay={overlay_expr}[bg_with_logo_{i}]")
        current_bg = f"[bg_with_logo_{i}]"
        input_idx += 1
        
    for i, text_path in enumerate(text_paths):
        cmd.extend(["-i", text_path])
        rotation = textRotations[i] if i < len(textRotations) and textRotations[i] is not None else 0
        rotation_expr = f"{rotation}*PI/180"
        
        tW = textWs[i] if i < len(textWs) else 100
        tH = textHs[i] if i < len(textHs) else None
        tX = textXs[i] if i < len(textXs) else 0
        tY = textYs[i] if i < len(textYs) else 0
        
        if tH is not None:
            rotate_filter = f"rotate={rotation_expr}:c=none:ow='hypot(iw,ih)':oh='hypot(iw,ih)'"
            overlay_expr = f"{tX}+{tW}/2-w/2:{tY}+{tH}/2-h/2"
        else:
            rotate_filter = f"rotate={rotation_expr}:c=none"
            overlay_expr = f"{tX}:{tY}"
            
        filters.append(f"[{input_idx}:v]scale={tW}:-1[t_scaled_{i}]")
        filters.append(f"[t_scaled_{i}]{rotate_filter}[t_rotated_{i}]")
        filters.append(f"{current_bg}[t_rotated_{i}]overlay={overlay_expr}[bg_with_text_{i}]")
        current_bg = f"[bg_with_text_{i}]"
        input_idx += 1
        
    if current_bg != "[bg]":
        filter_str = "; ".join(filters)
        cmd.extend(["-filter_complex", filter_str, "-map", current_bg])
        if muteAudio != "true":
            cmd.extend(["-map", "0:a?"])
    else:
        cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y}"])
        
    cmd.extend(["-c:v", "libx264", "-crf", crf, "-preset", preset])
    
    if muteAudio == "true":
        cmd.append("-an")
    else:
        cmd.extend(["-c:a", "copy"])
        
    cmd.append(output_path)
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
    
    while True:
        line = await process.stderr.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8')
        match = time_regex.search(line_str)
        if match and duration > 0:
            hrs, mins, secs = match.groups()
            current_time = int(hrs)*3600 + int(mins)*60 + float(secs)
            progress = int((current_time / duration) * 100)
            progress = min(99, progress)
            job_progress[job_id] = progress
            
            if job_id in active_connections:
                for ws in active_connections[job_id]:
                    try:
                        await ws.send_json({"progress": progress, "status": "processing"})
                    except:
                        pass
                        
    await process.wait()
    
    if process.returncode == 0:
        job_status[job_id] = "completed"
        job_progress[job_id] = 100
        if job_id in active_connections:
            for ws in active_connections[job_id]:
                try:
                    await ws.send_json({"progress": 100, "status": "completed"})
                except:
                    pass
    else:
        job_status[job_id] = "error"
        if job_id in active_connections:
            for ws in active_connections[job_id]:
                try:
                    await ws.send_json({"progress": 0, "status": "error", "detail": "FFmpeg failed"})
                except:
                    pass

@app.post("/api/process")
async def process_video(
    file: UploadFile = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    quality: str = Form("high"),
    muteAudio: str = Form("false"),
    trimStart: float = Form(None),
    trimEnd: float = Form(None),
    logoFiles: List[UploadFile] = File([]),
    logoXs: List[int] = Form([]),
    logoYs: List[int] = Form([]),
    logoWs: List[int] = Form([]),
    logoHs: List[int] = Form([]),
    logoRotations: List[float] = Form([]),
    logoOpacities: List[int] = Form([]),
    textFiles: List[UploadFile] = File([]),
    textXs: List[int] = Form([]),
    textYs: List[int] = Form([]),
    textWs: List[int] = Form([]),
    textHs: List[int] = Form([]),
    textRotations: List[float] = Form([])
):
    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".mp4" if file.filename else ".mp4"
    input_filename = f"{job_id}_in{ext}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    
    content = await file.read()
    with open(input_path, "wb") as f:
        f.write(content)
        
    logo_paths = []
    if logoFiles:
        for i, lf in enumerate(logoFiles):
            if not lf or not lf.filename: continue
            logo_ext = os.path.splitext(lf.filename)[1] or ".png"
            logo_filename = f"{job_id}_logo_{i}{logo_ext}"
            logo_path = os.path.join(UPLOAD_DIR, logo_filename)
            logo_content = await lf.read()
            with open(logo_path, "wb") as f:
                f.write(logo_content)
            logo_paths.append(logo_path)
            
    text_paths = []
    if textFiles:
        for i, tf in enumerate(textFiles):
            if not tf or not tf.filename: continue
            text_ext = os.path.splitext(tf.filename)[1] or ".png"
            text_filename = f"{job_id}_text_{i}{text_ext}"
            text_path = os.path.join(UPLOAD_DIR, text_filename)
            text_content = await tf.read()
            with open(text_path, "wb") as f:
                f.write(text_content)
            text_paths.append(text_path)
        
    output_filename = f"{job_id}_out.mp4"
    output_path = os.path.join(EXPORT_DIR, output_filename)
    
    asyncio.create_task(process_video_ffmpeg(
        job_id, input_path, output_path, 
        x, y, width, height, quality, muteAudio,
        trimStart, trimEnd, logo_paths, logoXs, logoYs, logoWs, logoHs, logoRotations, logoOpacities,
        text_paths, textXs, textYs, textWs, textHs, textRotations
    ))
    
    return {"job_id": job_id}

@app.websocket("/ws/progress/{job_id}")
async def progress_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)
    
    try:
        if job_id in job_progress:
            await websocket.send_json({
                "progress": job_progress.get(job_id, 0),
                "status": job_status.get(job_id, "processing")
            })
        
        while True:
            await asyncio.sleep(1)
            status = job_status.get(job_id)
            if status in ["completed", "error"]:
                break
    except WebSocketDisconnect:
        if websocket in active_connections.get(job_id, []):
            active_connections[job_id].remove(websocket)

@app.get("/api/download/{job_id}")
async def download_video(job_id: str, filename: str = "reframe_export.mp4"):
    output_filename = f"{job_id}_out.mp4"
    output_path = os.path.join(EXPORT_DIR, output_filename)
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type="video/mp4", filename=filename)
    return JSONResponse(status_code=404, content={"detail": "File not found"})

# Try to serve frontend statically if the directory exists
# This is useful for production (Docker)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
