import React, { useState } from 'react';
import { getVideoInfo, downloadVideo } from './api';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null); // formatId
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState('');

  const handleFetchInfo = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError('');
    setVideoData(null);

    try {
      const data = await getVideoInfo(url);
      console.log('Video Data Received:', data);
      setVideoData(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (formatId) => {
    if (!videoData?.job_id) return;
    setDownloading(formatId);
    try {
      // Pass the job_id so the worker knows which row to update
      await downloadVideo(url, formatId, videoData.job_id);
    } catch (err) {
      setError(err);
    } finally {
      setDownloading(null);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen w-full bg-[#0f172a] text-white flex flex-col items-center py-12 px-4 selection:bg-blue-500/30">
      
      {/* Header */}
      <div className="max-w-2xl w-full text-center space-y-4 mb-12">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent animate-fade-in">
          Video Downloader
        </h1>
        <p className="text-slate-400 text-lg">
          Download videos from YouTube, Instagram, TikTok, and more.
        </p>
      </div>

      {/* Search Input */}
      <div className="max-w-2xl w-full bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 p-6 rounded-3xl shadow-2xl transition-all hover:border-slate-600/50">
        <form onSubmit={handleFetchInfo} className="space-y-4">
          <div className="relative group">
            <input
              type="text"
              placeholder="Paste video URL here..."
              className="w-full bg-slate-900 border-2 border-transparent focus:border-blue-500/50 py-4 px-6 rounded-2xl outline-none transition-all placeholder:text-slate-600 text-lg pr-32"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading || !url}
              className={`absolute right-2 top-2 bottom-2 px-6 rounded-xl font-semibold transition-all flex items-center gap-2 ${
                loading || !url
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg active:scale-95'
              }`}
            >
              {loading ? (
                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Fetch'
              )}
            </button>
          </div>
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-sm flex items-center gap-3 animate-shake">
              <span className="text-lg">⚠️</span> {error}
            </div>
          )}
        </form>
      </div>

      {/* Result Display */}
      {videoData && (
        <div className="max-w-2xl w-full mt-8 animate-slide-up">
          <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl overflow-hidden shadow-2xl">
            <div className="md:flex">
              <div className="md:w-1/2 relative group overflow-hidden">
                <img
                  src={videoData.thumbnail}
                  alt={videoData.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60" />
                <span className="absolute bottom-4 right-4 bg-black/70 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-medium border border-white/10">
                  {formatDuration(videoData.duration)}
                </span>
              </div>
              <div className="md:w-1/2 p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-xl font-bold line-clamp-2 leading-snug group-hover:text-blue-400 transition-colors">
                    {videoData.title}
                  </h3>
                  <p className="mt-2 text-slate-400 text-sm flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    Available to download
                  </p>
                </div>
                
                <div className="mt-6 space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                  {videoData?.formats && videoData.formats.length > 0 ? (
                    videoData.formats.map((format) => (
                      <button
                        key={format.format_id}
                        onClick={() => handleDownload(format.format_id)}
                        disabled={downloading !== null}
                        className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-900/50 border border-slate-700/50 hover:bg-slate-700/50 hover:border-blue-500/30 transition-all group/item"
                      >
                        <div className="text-left">
                          <p className="text-sm font-semibold text-slate-200 group-hover/item:text-blue-300 transition-colors uppercase">
                            {format.quality} ({format.ext})
                          </p>
                          <p className="text-xs text-slate-500">{formatSize(format.filesize)}</p>
                        </div>
                        {downloading === format.format_id ? (
                          <div className="h-5 w-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                        ) : (
                          <span className="text-slate-400 group-hover/item:text-blue-400 transition-colors">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </span>
                        )}
                      </button>
                    ))
                  ) : (
                    <p className="text-slate-500 text-center text-sm italic">No compatible formats found.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer / Features */}
      {!videoData && !loading && (
        <div className="max-w-2xl w-full grid grid-cols-2 md:grid-cols-4 gap-4 mt-12 opacity-60">
            {['YouTube', 'Instagram', 'TikTok', 'X/Twitter'].map(plat => (
                <div key={plat} className="flex flex-col items-center justify-center p-4 rounded-2xl bg-slate-800/30 border border-slate-700/50 text-xs font-medium uppercase tracking-widest text-slate-400">
                    {plat}
                </div>
            ))}
        </div>
      )}

      {/* Animations via style tag for simplicity in this artifact */}
      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); } 20%, 40%, 60%, 80% { transform: translateX(2px); } }
        .animate-fade-in { animation: fadeIn 0.8s ease-out; }
        .animate-slide-up { animation: slideUp 0.6s ease-out; }
        .animate-shake { animation: shake 0.5s ease-in-out; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.2); }
      `}</style>
    </div>
  );
}

export default App;
