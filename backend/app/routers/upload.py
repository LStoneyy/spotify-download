from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional

from ..database import get_session, get_settings
from ..downloader import sanitize_filename, _set_metadata

router = APIRouter()

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/music")

ACCEPTED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/x-flac",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/ogg",
    "audio/x-ogg",
    "audio/wma",
    "audio/x-ms-wma",
    "audio/aac",
    "audio/x-aac",
    "audio/opus",
    "audio/webm",
}

ACCEPTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma", ".aac", ".opus", ".webm"}


class UploadResponse(BaseModel):
    ok: bool
    file_path: str
    message: Optional[str] = None


def _convert_to_mp3(input_path: str, output_path: str, quality: str) -> None:
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-codec:a", "libmp3lame",
        "-b:a", f"{quality}k",
        "-y",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: str = Form(...),
    album: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ACCEPTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Accepted formats: {', '.join(ACCEPTED_EXTENSIONS)}",
        )

    if file.content_type and file.content_type not in ACCEPTED_MIME_TYPES:
        if ext not in ACCEPTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type: {file.content_type}",
            )

    settings = get_settings(session)
    file_name = sanitize_filename(settings.file_template, title, artist, album or "")
    if not file_name:
        raise HTTPException(status_code=400, detail="Empty filename after sanitization")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_path = os.path.join(OUTPUT_DIR, f"{file_name}.mp3")
    
    if os.path.exists(final_path):
        raise HTTPException(status_code=409, detail=f"File already exists: {file_name}.mp3")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        try:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name
        except Exception as e:
            os.unlink(tmp_file.name)
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    try:
        if ext == ".mp3":
            shutil.copy2(tmp_path, final_path)
        else:
            _convert_to_mp3(tmp_path, final_path, settings.quality)
        
        _set_metadata(final_path, title, artist, album)
        
        return UploadResponse(ok=True, file_path=final_path, message="File uploaded successfully")
    
    except Exception as e:
        if os.path.exists(final_path):
            os.unlink(final_path)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
