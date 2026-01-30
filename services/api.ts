import axios from 'axios';
import { VideoData } from '../types';

// Detect environment: 
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal ? 'http://localhost:8000/api' : '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Increased timeout to 25s. 
  // Vercel Free tier limits to 10s server-side, but this ensures client doesn't give up too early 
  // if you upgrade plans or run locally.
  timeout: 25000, 
});

const MOCK_DATA: VideoData = {
  id: 'demo-video-1',
  title: 'Demo Mode: Backend Disconnected (Localhost)',
  thumbnail: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/800px-Big_buck_bunny_poster_big.jpg',
  duration: 596,
  platform: 'Demo Mode',
  download_url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
  ext: 'mp4',
  isMock: true,
};

export const fetchVideoInfo = async (url: string): Promise<VideoData> => {
  try {
    const response = await apiClient.get<VideoData>('/info', {
      params: { url },
    });
    return response.data;
  } catch (error: any) {
    console.warn('API Error:', error);
    
    // CASE 1: Server Responded with Error (4xx, 5xx)
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail;

      if (status === 504) {
        throw new Error("Server Timeout: The video took too long to process. TikTok might be slow right now.");
      }
      if (status === 403) {
         throw new Error(detail || "Access Denied: The server was blocked by the platform.");
      }
      
      throw new Error(detail || `Server Error (${status}): Please try again.`);
    } 
    
    // CASE 2: Network Error (Request made, no response)
    else if (error.request) {
      // Only fallback to Mock Data if we are on Localhost (developers machine)
      // On Production/Vercel, we want to show the real "Network Error" to debug.
      if (isLocal) {
        console.warn('Local backend unavailable, showing demo data.');
        await new Promise(resolve => setTimeout(resolve, 1500));
        return {
          ...MOCK_DATA,
          title: `DEMO RESULT: ${url.slice(0, 30)}...`,
        };
      }
      
      throw new Error("Network Error: Could not reach the backend. Please check your internet connection.");
    } 
    
    // CASE 3: Setup Error
    else {
      throw new Error(error.message || 'Unknown Error occurred.');
    }
  }
};

export const getDownloadLink = (videoData: VideoData): string => {
  if (videoData.isMock) {
    return videoData.download_url;
  }
  const params = new URLSearchParams({
    url: videoData.download_url,
    title: videoData.title,
    ext: videoData.ext,
  });
  return `${API_BASE_URL}/download?${params.toString()}`;
};