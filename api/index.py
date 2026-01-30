from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from yt_dlp import YoutubeDL
import requests
import urllib.parse
import os

app = FastAPI()

# Configure CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
async def health_check():
    return {"status": "ok", "message": "Umii Video Downloader Backend is Running"}

def get_video_info(url: str):
    # Vercel file system is read-only, use /tmp for cache
    # We add User-Agent headers to look like a real browser (Chrome on Windows)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'cache_dir': '/tmp/yt-dlp-cache',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    
    try:
        # Create cache dir if it doesn't exist
        os.makedirs('/tmp/yt-dlp-cache', exist_ok=True)
        
        with YoutubeDL(ydl_opts) as ydl:
            # extract_info with download=False fetches metadata
            info = ydl.extract_info(url, download=False)
            
            return {
                "id": info.get('id'),
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "platform": info.get('extractor_key'),
                "download_url": info.get('url'),
                "ext": info.get('ext', 'mp4')
            }
    except Exception as e:
        print(f"Error extracting info: {str(e)}")
        # We return None here to let the API handler raise the specific HTTP exception
        return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL of the video to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        data = get_video_info(url)
        if not data:
            # If data is None, it means yt-dlp failed (likely blocking or invalid URL)
            return JSONResponse(
                status_code=400, 
                content={"detail": "Could not extract video. The link might be private, or the platform blocked the request."}
            )
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Server Error: {str(e)}"})

@app.get("/api/download")
async def download(
    url: str = Query(..., description="The direct video URL from yt-dlp"), 
    title: str = Query("video", description="Filename for the download"),
    ext: str = Query("mp4", description="File extension")
):
    try:
        # Request headers to avoid 403 Forbidden on the video file itself
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        r = requests.get(url, stream=True, headers=headers)
        r.raise_for_status()
        
        safe_filename = urllib.parse.quote(f"{title}.{ext}")
        
        return StreamingResponse(
            r.iter_content(chunk_size=8192),
            media_type=r.headers.get("Content-Type", "video/mp4"),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
