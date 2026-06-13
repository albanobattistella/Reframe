import asyncio
import os
import re
import uuid
import subprocess
import json
import base64
from fastapi import FastAPI, UploadFile, Form, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

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
FONTS_DIR = "/app/fonts" if os.environ.get("DOCKER") else os.path.join(os.getcwd(), "fonts")
FRONTEND_DIR = "/app/frontend" if os.environ.get("DOCKER") else os.path.join(os.path.dirname(os.getcwd()), "frontend", "dist")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

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

def get_video_dimensions(filepath: str) -> tuple[int, int]:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of",
             "csv=p=0", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        w, h = result.stdout.strip().split(',')
        return int(w), int(h)
    except Exception:
        return 1920, 1080

def create_text_image(t_item: dict, output_path: str, cw: int) -> tuple[int, int]:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        content = t_item.get("content", "")
        color = t_item.get("color", "#ffffff")
        shadow = t_item.get("shadow", True)
        
        rel_scale = t_item.get("relativeScale", 0)
        if rel_scale <= 0:
            rel_scale = 1.0 / 800.0
            
        font_size = int(24 * rel_scale * cw)
        if font_size < 10: font_size = 10
        
        img = Image.new('RGBA', (4000, 4000), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        
        font_name = t_item.get("font", "Arial")
        font_map = {
            "Fira Code": "/usr/share/fonts/truetype/firacode/FiraCode-Regular.ttf",
            "Arial": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "Verdana": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "Tahoma": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "Inter": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        }
        
        custom_font_path = None
        if os.path.exists(FONTS_DIR):
            for f in os.listdir(FONTS_DIR):
                if os.path.splitext(f)[0] == font_name:
                    custom_font_path = os.path.join(FONTS_DIR, f)
                    break
        
        if custom_font_path and os.path.exists(custom_font_path):
            font_file = custom_font_path
        else:
            font_file = font_map.get(font_name, "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
        
        try:
            font = ImageFont.truetype(font_file, font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
                
        lines = content.split('\n')
        padding_x = int(font_size * 0.4)
        padding_y = int(font_size * 0.4)
        y_offset = padding_y
        x_offset = padding_x
        
        if shadow:
            shadow_img = Image.new('RGBA', (4000, 4000), (0, 0, 0, 0))
            d_shadow = ImageDraw.Draw(shadow_img)
            sy_offset = y_offset
            for line in lines:
                d_shadow.text((x_offset, sy_offset), line, font=font, fill=(0,0,0,255))
                sy_offset += int(font_size * 1.2)
            
            blur_radius = max(3, int(font_size * 0.12))
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            shadow_offset_x = max(2, int(font_size*0.06))
            shadow_offset_y = max(2, int(font_size*0.06))
            for _ in range(4):
                img.alpha_composite(shadow_img, (shadow_offset_x, shadow_offset_y))

        for line in lines:
            d.text((x_offset, y_offset), line, font=font, fill=color)
            y_offset += int(font_size * 1.2)
            
        bbox = img.getbbox()
        if bbox:
            img = img.crop((0, 0, bbox[2] + padding_x, bbox[3] + padding_y))
        else:
            img = Image.new('RGBA', (10, 10), (255, 255, 255, 0))
            
        img.save(output_path)
        return img.width, img.height
    except Exception as e:
        print(f"Error creating text image: {e}")
        img = Image.new('RGBA', (10, 10), (255, 255, 255, 0))
        img.save(output_path)
        return 10, 10

async def process_video_ffmpeg(
    job_id: str, 
    input_path: str, 
    output_path: str, 
    x: int, y: int, w: int, h: int, 
    quality: str, 
    muteAudio: str,
    useGpu: str = "false",
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
    if useGpu == "true":
        qp = "20" if quality == "high" else "24"
    else:
        crf = "18" if quality == "high" else "23"
        preset = "slow" if quality == "high" else "fast"
    
    cmd = ["ffmpeg", "-y"]
    
    if useGpu == "true":
        cmd.extend(["-vaapi_device", "/dev/dri/renderD128"])
    
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
        if useGpu == "true":
            filters.append(f"{current_bg}format=nv12,hwupload[hw]")
            current_bg = "[hw]"
        filter_str = "; ".join(filters)
        cmd.extend(["-filter_complex", filter_str, "-map", current_bg])
        if muteAudio != "true":
            cmd.extend(["-map", "0:a?"])
    else:
        if useGpu == "true":
            cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y},format=nv12,hwupload"])
        else:
            cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y}"])
        
    if useGpu == "true":
        cmd.extend(["-c:v", "h264_vaapi", "-qp", qp])
    else:
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
    useGpu: str = Form("false"),
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
        x, y, width, height, quality, muteAudio, useGpu,
        trimStart, trimEnd, logo_paths, logoXs, logoYs, logoWs, logoHs, logoRotations, logoOpacities,
        text_paths, textXs, textYs, textWs, textHs, textRotations
    ))
    
    return {"job_id": job_id}

@app.post("/api/automate")
async def automate_process(
    video: UploadFile = File(...),
    config: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    ext = os.path.splitext(video.filename)[1] or ".mp4" if video.filename else ".mp4"
    input_filename = f"{job_id}_in{ext}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    
    # Save video
    content = await video.read()
    with open(input_path, "wb") as f:
        f.write(content)
        
    # Read config
    config_content = await config.read()
    settings = json.loads(config_content.decode('utf-8'))
    
    vw, vh = get_video_dimensions(input_path)
    vr = vw / vh
    
    preset = settings.get("selectedPreset", {})
    if preset.get("id") == "custom":
        tr = settings.get("customRatioW", 16) / settings.get("customRatioH", 9)
    else:
        tr = preset.get("ratio", 9/16)
        
    if tr > vr:
        cw = vw
        ch = vw / tr
    else:
        ch = vh
        cw = vh * tr
        
    cw = int(cw)
    ch = int(ch)
    x = int((vw - cw) / 2)
    y = int((vh - ch) / 2)
    
    logo_paths, logoXs, logoYs, logoWs, logoHs, logoRotations, logoOpacities = [], [], [], [], [], [], []
    for i, w in enumerate(settings.get("watermarks", [])):
        if "fileBase64" in w and w["fileBase64"]:
            b64 = w["fileBase64"].split(",")[1] if "," in w["fileBase64"] else w["fileBase64"]
            img_data = base64.b64decode(b64)
            logo_ext = ".png"
            if w.get("fileMime") == "image/jpeg": logo_ext = ".jpg"
            elif w.get("fileMime") == "image/svg+xml": logo_ext = ".svg"
            
            logo_path = os.path.join(UPLOAD_DIR, f"{job_id}_logo_{i}{logo_ext}")
            with open(logo_path, "wb") as f:
                f.write(img_data)
                
            try:
                with Image.open(logo_path) as im:
                    im_w, im_h = im.size
                logo_w = int(150 * w.get("relativeScale", 0) * cw)
                logo_h = int(logo_w * (im_h / im_w)) if im_w > 0 else logo_w
            except:
                logo_w = int(150 * w.get("relativeScale", 0) * cw)
                logo_h = None
                
            logo_paths.append(logo_path)
            logoWs.append(logo_w)
            logoHs.append(logo_h)
            logoXs.append(int(w.get("relativeX", 0) * cw))
            logoYs.append(int(w.get("relativeY", 0) * ch))
            logoRotations.append(w.get("rotation", 0))
            logoOpacities.append(w.get("opacity", 100))
            
    text_paths, textXs, textYs, textWs, textHs, textRotations = [], [], [], [], [], []
    for i, t in enumerate(settings.get("texts", [])):
        if t.get("content"):
            text_path = os.path.join(UPLOAD_DIR, f"{job_id}_text_{i}.png")
            img_w, img_h = create_text_image(t, text_path, cw)
            text_paths.append(text_path)
            textWs.append(img_w)
            textHs.append(img_h)
            textXs.append(int(t.get("relativeX", 0) * cw))
            textYs.append(int(t.get("relativeY", 0) * ch))
            textRotations.append(t.get("rotation", 0))
            
    output_filename = f"{job_id}_out.mp4"
    output_path = os.path.join(EXPORT_DIR, output_filename)
    
    quality = settings.get("quality", "high")
    muteAudio = "true" if settings.get("muteAudio") else "false"
    useGpu = "true" if settings.get("useGpu") else "false"
    trimStart = settings.get("trimStart")
    trimEnd = settings.get("trimEnd")
    
    await process_video_ffmpeg(
        job_id, input_path, output_path,
        x, y, cw, ch, quality, muteAudio, useGpu,
        trimStart, trimEnd, logo_paths, logoXs, logoYs, logoWs, logoHs, logoRotations, logoOpacities,
        text_paths, textXs, textYs, textWs, textHs, textRotations
    )
    
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type="video/mp4", filename=f"automated_{video.filename}")
    return JSONResponse(status_code=500, content={"detail": "Video processing failed"})

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

@app.get("/api/media")
async def list_media():
    uploads = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(path):
                uploads.append({
                    "filename": f,
                    "size": os.path.getsize(path),
                    "created": os.path.getctime(path)
                })
    
    exports = []
    if os.path.exists(EXPORT_DIR):
        for f in os.listdir(EXPORT_DIR):
            path = os.path.join(EXPORT_DIR, f)
            if os.path.isfile(path):
                exports.append({
                    "filename": f,
                    "size": os.path.getsize(path),
                    "created": os.path.getctime(path)
                })
                
    # Sort descending by creation time
    uploads.sort(key=lambda x: x["created"], reverse=True)
    exports.sort(key=lambda x: x["created"], reverse=True)
    
    return {"uploads": uploads, "exports": exports}

@app.delete("/api/media/{folder}/{filename}")
async def delete_media(folder: str, filename: str):
    if folder == "uploads":
        file_path = os.path.join(UPLOAD_DIR, filename)
    elif folder == "exports":
        file_path = os.path.join(EXPORT_DIR, filename)
    else:
        return JSONResponse(status_code=400, content={"detail": "Invalid folder"})
        
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return {"status": "success"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Failed to delete file: {str(e)}"})
    return JSONResponse(status_code=404, content={"detail": "File not found"})

@app.delete("/api/media/{folder}")
async def delete_all_media(folder: str):
    if folder == "uploads":
        target_dir = UPLOAD_DIR
    elif folder == "exports":
        target_dir = EXPORT_DIR
    else:
        return JSONResponse(status_code=400, content={"detail": "Invalid folder"})
        
    if os.path.exists(target_dir):
        try:
            for f in os.listdir(target_dir):
                file_path = os.path.join(target_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return {"status": "success"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Failed to delete files: {str(e)}"})
    return JSONResponse(status_code=404, content={"detail": "Folder not found"})

@app.get("/api/fonts")
async def list_fonts():
    fonts = ["Fira Code", "Arial", "Verdana", "Tahoma", "Inter"]
    custom_fonts = []
    if os.path.exists(FONTS_DIR):
        for f in os.listdir(FONTS_DIR):
            if f.lower().endswith(('.ttf', '.otf')):
                font_name = os.path.splitext(f)[0]
                if font_name not in fonts:
                    custom_fonts.append(font_name)
    
    return {"static": fonts, "custom": custom_fonts}

@app.post("/api/fonts")
async def upload_font(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.ttf', '.otf')):
        return JSONResponse(status_code=400, content={"detail": "Only .ttf and .otf files are allowed"})
        
    font_path = os.path.join(FONTS_DIR, file.filename)
    content = await file.read()
    with open(font_path, "wb") as f:
        f.write(content)
        
    return {"status": "success", "font": os.path.splitext(file.filename)[0]}

@app.get("/api/fonts/{font_name}/file")
async def get_font_file(font_name: str):
    font_map = {
        "Fira Code": "/usr/share/fonts/truetype/firacode/FiraCode-Regular.ttf",
        "Arial": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "Verdana": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "Tahoma": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "Inter": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    }
    
    if os.path.exists(FONTS_DIR):
        for f in os.listdir(FONTS_DIR):
            if os.path.splitext(f)[0] == font_name:
                return FileResponse(os.path.join(FONTS_DIR, f))
                
    if font_name in font_map and os.path.exists(font_map[font_name]):
        return FileResponse(font_map[font_name])
        
    return JSONResponse(status_code=404, content={"detail": "Font file not found"})

@app.delete("/api/fonts/{font_name}")
async def delete_font(font_name: str):
    if os.path.exists(FONTS_DIR):
        for f in os.listdir(FONTS_DIR):
            if os.path.splitext(f)[0] == font_name:
                os.remove(os.path.join(FONTS_DIR, f))
                return {"status": "success"}
    return JSONResponse(status_code=404, content={"detail": "Font not found"})

# Try to serve frontend statically if the directory exists
# This is useful for production (Docker)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

