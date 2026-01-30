import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from yt_dlp import YoutubeDL
import urllib.parse

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
    "*" # Allow all for MVP/development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_video_info(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',  # Best quality
        'outtmpl': '%(title)s.%(ext)s',
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant data
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
        print(f"Error extracting info: {e}")
        return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL of the video to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    data = get_video_info(url)
    if not data:
        raise HTTPException(status_code=400, detail="Could not extract video info. Verify the URL is public and valid.")
    
    return data

@app.get("/api/download")
async def download(
    url: str = Query(..., description="The direct video URL from yt-dlp"), 
    title: str = Query("video", description="Filename for the download"),
    ext: str = Query("mp4", description="File extension")
):
    """
    Proxy endpoint to stream video data from the source to the client.
    This bypasses CORS restrictions often placed on direct video links (like googlevideo.com).
    """
    try:
        # Stream the content from the upstream URL
        # We use stream=True to avoid loading the whole file into memory
        r = requests.get(url, stream=True)
        r.raise_for_status()
        
        # Sanitize filename
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
