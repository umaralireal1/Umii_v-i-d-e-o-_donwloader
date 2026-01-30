import axios from 'axios';
import { VideoData } from '../types';

// Detect environment: 
// On Vercel (Production), we use relative path '/api' which routes to api/index.py
// On Local, we use 'http://localhost:8000/api' if the user is running the python server separately,
// OR if using `vite proxy`, relative path would work too. 
// For safety, we check if we are on localhost.
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal ? 'http://localhost:8000/api' : '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // Increased timeout to 15s as yt-dlp can be slow
});

// Mock data for demo/fallback purposes
const MOCK_DATA: VideoData = {
  id: 'demo-video-1',
  title: 'Demo Mode: Big Buck Bunny (Backend Offline or Blocked)',
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
    
    // Check if it's an actual response from the server (e.g. 400 Bad Request, 500 Server Error)
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const serverMessage = error.response.data?.detail || 'Server returned an error';
      throw new Error(serverMessage); 
    } else if (error.request) {
      // The request was made but no response was received (Network Error)
      console.warn('Backend unavailable/Network Error, falling back to demo mode.');
      
      // Simulate network delay for realistic UX
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      return {
        ...MOCK_DATA,
        title: `DEMO RESULT: ${url.slice(0, 30)}${url.length > 30 ? '...' : ''}`,
      };
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error('Error setting up request');
    }
  }
};

export const getDownloadLink = (videoData: VideoData): string => {
  // If we are in mock mode, return the direct URL (the proxy won't work)
  if (videoData.isMock) {
    return videoData.download_url;
  }

  // Construct the proxy URL
  const params = new URLSearchParams({
    url: videoData.download_url,
    title: videoData.title,
    ext: videoData.ext,
  });
  return `${API_BASE_URL}/download?${params.toString()}`;
};