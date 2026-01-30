from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from yt_dlp import YoutubeDL
import requests
import urllib.parse
import os

app = FastAPI()

# Configure CORS - Allow all for maximum compatibility
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
    return {"status": "ok", "message": "Umii Video Downloader Backend is Online"}

def get_video_info(url: str):
    # Optimizations for Vercel (Speed & Stealth)
    ydl_opts = {
        'format': 'best', # 'best' is faster than specific video+audio merge
        'outtmpl': '%(title)s.%(ext)s',
        'cache_dir': '/tmp/yt-dlp-cache',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Restrict info to speed up processing
        'skip_download': True,
        # Stealth headers to mimic a real desktop user
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    
    # Specific adjustments for TikTok to avoid 403s/Captchas
    if "tiktok.com" in url:
        # Sometimes forcing the mobile API via user agent works better, 
        # but modern TikTok often prefers desktop emulation for public links.
        pass

    try:
        os.makedirs('/tmp/yt-dlp-cache', exist_ok=True)
        
        with YoutubeDL(ydl_opts) as ydl:
            # download=False is crucial for speed
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
        error_str = str(e)
        print(f"Extraction Error: {error_str}")
        # Return the specific error so the frontend displays it
        return {"error": error_str}

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL of the video to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    result = get_video_info(url)
    
    # Check if yt-dlp returned a dictionary with an error key
    if result and "error" in result:
        # If it's a 403 or specific blocking message, pass it through
        error_msg = result["error"]
        if "HTTP Error 403" in error_msg:
            return JSONResponse(status_code=403, content={"detail": "Access Denied by Platform. Try a different link or try again later."})
        if "Sign in to confirm" in error_msg:
             return JSONResponse(status_code=403, content={"detail": "This video requires login (Private/Age-gated)."})
        return JSONResponse(status_code=400, content={"detail": f"Extraction Failed: {error_msg}"})
        
    if not result:
        return JSONResponse(
            status_code=400, 
            content={"detail": "Could not extract video. Link might be invalid or the server timed out."}
        )
    
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="The direct video URL from yt-dlp"), 
    title: str = Query("video", description="Filename for the download"),
    ext: str = Query("mp4", description="File extension")
):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
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
        raise HTTPException(status_code=500, detail=f"Download Proxy Failed: {str(e)}")
