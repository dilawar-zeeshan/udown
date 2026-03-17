import axios from 'axios';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

const api = axios.create({
  baseURL: `${SUPABASE_URL}/functions/v1`,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
    'apikey': SUPABASE_ANON_KEY,
  }
});

const restApi = axios.create({
  baseURL: `${SUPABASE_URL}/rest/v1`,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
    'apikey': SUPABASE_ANON_KEY,
  }
});

const pollJob = async (jobId, targetStatus, onProgress, maxAttempts = 30) => {
  for (let i = 0; i < maxAttempts; i++) {
    const { data } = await restApi.get(`/downloads_queue?id=eq.${jobId}&select=*`);
    const job = data[0];
    
    if (job) {
      if (onProgress) onProgress(job.status);
      if (job.status === targetStatus || job.status === 'done') return job;
      if (job.status === 'failed') throw new Error(job.error_message || 'Job failed');
    }
    
    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error('Polling timed out. The worker might be busy.');
};

// Helper to get or create a session ID
const getSessionId = () => {
    let sessionId = localStorage.getItem('vdownloader_session_id');
    if (!sessionId) {
        sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        localStorage.setItem('vdownloader_session_id', sessionId);
    }
    return sessionId;
};

export const getVideoInfo = async (url, onProgress) => {
  try {
    const sessionId = getSessionId();
    const response = await api.post('/video-info', { url, session_id: sessionId });
    const { job_id } = response.data;
    
    // Wait for the GHA worker to fetch metadata
    const job = await pollJob(job_id, 'awaiting_format', onProgress);
    return { ...job.video_metadata, job_id };
  } catch (error) {
    console.error('Error fetching video info:', error);
    throw error.response?.data?.error || error.message || 'Failed to fetch video information.';
  }
};

export const downloadVideo = async (url, formatId, jobId, title = 'video', onProgress) => {
  try {
    const sessionId = getSessionId();
    // 1. Tell the edge function to start the download
    await api.post('/download-proxy', { url, format_id: formatId, job_id: jobId, session_id: sessionId });
    
    // 2. Poll for the final result URL
    const job = await pollJob(jobId, 'done', onProgress, 60); 
    
    if (job.result_url) {
      // 3. Instead of direct Link, use our serve-video Edge Function
      const downloadUrl = `${SUPABASE_URL}/functions/v1/serve-video?job_id=${jobId}`;
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      // Note: The Edge Function provides the filename via Content-Disposition
      link.setAttribute('download', (title || 'video').replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.mp4');
      link.target = "_self";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } else {
      throw new Error('Download link not found in response');
    }
  } catch (error) {
    console.error('Error downloading video:', error);
    throw error.response?.data?.error || error.message || 'Download failed.';
  }
};
