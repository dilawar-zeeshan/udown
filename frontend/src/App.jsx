import React, { useState, useEffect } from 'react';
import { getVideoInfo, downloadVideo } from './api';

const STATUS_CONFIG = {
  'pending_info': { label: 'Queueing Request...', color: 'text-blue-400', icon: '🔍' },
  'awaiting_format': { label: 'Formats Ready', color: 'text-green-400', icon: '✅' },
  'pending_download': { label: 'Waking up Worker...', color: 'text-blue-400', icon: '🚀' },
  'processing': { label: 'Downloading Video...', color: 'text-indigo-400', icon: '📥' },
  'done': { label: 'Download Complete!', color: 'text-green-400', icon: '🏁' },
  'failed': { label: 'Error Occurred', color: 'text-red-400', icon: '⚠️' }
};

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null); // formatId
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState(null);

  const handleFetchInfo = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError('');
    setVideoData(null);
    setStatus('pending_info');

    try {
      const data = await getVideoInfo(url, (newStatus) => setStatus(newStatus));
      setVideoData(data);
    } catch (err) {
      setError(err);
      setStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (formatId) => {
    if (!videoData?.job_id) return;
    setDownloading(formatId);
    setStatus('pending_download');
    try {
      await downloadVideo(url, formatId, videoData.job_id, videoData.title, (newStatus) => setStatus(newStatus));
      setStatus('done');
    } catch (err) {
      setError(err);
      setStatus('failed');
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
    <main className="min-h-screen w-full flex flex-col items-center justify-start lg:justify-center py-12 px-4 selection:bg-blue-500/30">
      
      {/* Background Decor */}
      <div className="fixed inset-0 -z-10 bg-[#0f172a]" />
      <div className="fixed top-0 right-0 w-[300px] md:w-[600px] h-[300px] md:h-[600px] bg-blue-500/10 blur-[100px] md:blur-[150px] rounded-full -z-10 animate-pulse-soft" />
      <div className="fixed bottom-0 left-0 w-[300px] md:w-[600px] h-[300px] md:h-[600px] bg-indigo-500/10 blur-[100px] md:blur-[150px] rounded-full -z-10 animate-pulse-soft" />

      {/* Header Container */}
      <div className="max-w-4xl w-full text-center space-y-6 mb-12 animate-float">
        <div className="inline-block px-4 py-1.5 mb-2 rounded-full bg-slate-800/60 border border-slate-700/50 backdrop-blur-md text-xs font-bold tracking-widest text-blue-400 uppercase">
          Serverless Worker Edition
        </div>
        <h1 className="text-5xl sm:text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-2xl leading-[1.1]">
          V<span className="text-gradient">Downloader</span>
        </h1>
        <p className="text-slate-400 text-lg md:text-xl font-medium max-w-xl mx-auto leading-relaxed px-4">
          Premium cloud-based downloader for social media, powered by GitHub Actions.
        </p>
      </div>

      {/* Main Action Area */}
      <div className="max-w-3xl w-full glass-card p-6 md:p-10 rounded-[2rem] md:rounded-[3rem] shadow-2xl transition-all duration-300">
        <form onSubmit={handleFetchInfo} className="space-y-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <input
              type="text"
              placeholder="Paste your video link here..."
              className="flex-1 glass-input py-4 md:py-6 px-6 md:px-8 rounded-2xl md:rounded-3xl text-base md:text-lg placeholder:text-slate-500 shadow-inner"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading || !url}
              className="btn-primary flex items-center justify-center gap-3 py-4 md:py-6"
            >
              {loading ? (
                <div className="h-5 w-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span className="font-bold uppercase tracking-wider">Analyze</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
          
          {/* Status Tracker */}
          {status && (
            <div className={`flex items-center justify-center gap-4 py-3 rounded-2xl bg-white/5 border border-white/5 text-sm font-bold uppercase tracking-widest animate-fade-in ${STATUS_CONFIG[status]?.color}`}>
              <span className="text-xl">{STATUS_CONFIG[status]?.icon}</span>
              {STATUS_CONFIG[status]?.label}
              {loading && <div className="flex gap-1"><span className="animate-bounce">.</span><span className="animate-bounce delay-100">.</span><span className="animate-bounce delay-200">.</span></div>}
            </div>
          )}

          {error && (
            <div className="p-6 bg-red-500/10 border-2 border-red-500/20 text-red-400 rounded-3xl animate-shake">
              <div className="flex items-start gap-4">
                <span className="text-2xl mt-1">⚠️</span> 
                <div>
                  <p className="font-black uppercase tracking-tighter mb-1 text-lg">System Error</p>
                  <p className="opacity-80 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Results Container */}
      {videoData && (
        <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12 animate-slide-up px-4">
          {/* Visual Presentation */}
          <div className="glass-card rounded-[2.5rem] overflow-hidden group border-2 border-white/5">
            <div className="relative aspect-video overflow-hidden">
              <img
                src={videoData.thumbnail}
                alt={videoData.title}
                className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/40 to-transparent opacity-90" />
              <div className="absolute bottom-8 left-8 right-8 flex items-end justify-between">
                <div className="glass-card px-4 py-2 rounded-xl text-xs font-black tracking-widest border border-white/20">
                  {formatDuration(videoData.duration)}
                </div>
                <div className="bg-blue-600 p-4 rounded-2xl shadow-xl shadow-blue-900/40 scale-0 group-hover:scale-100 transition-transform duration-500">
                   <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                   </svg>
                </div>
              </div>
            </div>
            <div className="p-10 space-y-6">
              <h3 className="text-3xl font-black leading-tight text-white group-hover:text-blue-400 transition-colors">
                {videoData.title}
              </h3>
              <div className="flex flex-wrap gap-3">
                 <span className="px-4 py-1.5 rounded-full glass-card text-[10px] uppercase font-black tracking-widest text-slate-400">MP4 HD</span>
                 <span className="px-4 py-1.5 rounded-full glass-card text-[10px] uppercase font-black tracking-widest text-slate-400">Fast Cloud Link</span>
                 <span className="px-4 py-1.5 rounded-full bg-green-500/10 text-[10px] uppercase font-black tracking-widest text-green-400 border border-green-500/20">Verified Info</span>
              </div>
            </div>
          </div>

          {/* Download Options */}
          <div className="glass-card rounded-[2.5rem] p-8 md:p-10 flex flex-col border-2 border-white/5">
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center border border-blue-500/20">
                 <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                 </svg>
              </div>
              <h4 className="text-xl font-black tracking-tight">Format selection</h4>
            </div>
            
            <div className="space-y-4 flex-1 overflow-y-auto pr-3 custom-scrollbar max-h-[400px]">
              {videoData?.formats && videoData.formats.length > 0 ? (
                videoData.formats.map((format) => (
                  <button
                    key={format.format_id}
                    onClick={() => handleDownload(format.format_id)}
                    disabled={downloading !== null}
                    className={`w-full group/item flex items-center justify-between p-6 rounded-[2rem] transition-all border-2 relative overflow-hidden ${
                      downloading === format.format_id 
                        ? 'bg-blue-600/20 border-blue-500/50' 
                        : 'bg-slate-950/40 border-transparent hover:border-blue-500/30 hover:bg-slate-900/40'
                    }`}
                  >
                    <div className="text-left relative z-10">
                      <p className="text-lg font-black text-white group-hover/item:text-blue-400 transition-colors uppercase leading-none">
                        {format.quality}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{format.ext}</span>
                        <div className="w-1 h-1 bg-slate-700 rounded-full" />
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{formatSize(format.filesize)}</span>
                      </div>
                    </div>
                    <div className="relative z-10">
                      {downloading === format.format_id ? (
                        <div className="h-8 w-8 border-4 border-blue-500/30 border-t-blue-400 rounded-full animate-spin" />
                      ) : (
                        <div className="bg-slate-800 p-3 rounded-2xl border border-white/5 group-hover/item:bg-blue-600 group-hover/item:text-white group-hover/item:shadow-xl group-hover/item:shadow-blue-500/30 transition-all transform group-hover/item:scale-110">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </button>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-slate-500 space-y-4">
                  <div className="p-4 bg-slate-800/40 rounded-3xl animate-pulse">
                    <svg className="w-12 h-12 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="italic font-bold tracking-tight uppercase text-xs">No suitable formats found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Social Proof / Brands */}
      {!videoData && !loading && (
        <div className="max-w-5xl w-full grid grid-cols-2 lg:grid-cols-4 gap-6 mt-16 animate-fade-in">
            {[
              { name: 'YouTube', icon: '🔴' },
              { name: 'Instagram', icon: '📸' },
              { name: 'TikTok', icon: '🎵' },
              { name: 'X / Twitter', icon: '🐦' }
            ].map(plat => (
                <div key={plat.name} className="glass-card flex flex-col items-center justify-center py-10 rounded-[2.5rem] opacity-60 hover:opacity-100 transition-all hover:bg-slate-800/80 hover:scale-105 cursor-default group">
                    <span className="text-3xl mb-3 transform group-hover:scale-125 transition-transform duration-500">{plat.icon}</span>
                    <span className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500 group-hover:text-blue-400 transition-colors">{plat.name}</span>
                </div>
            ))}
        </div>
      )}

      <footer className="mt-auto py-16 text-slate-500 text-[10px] font-black uppercase tracking-[0.5em] text-center opacity-40 hover:opacity-100 transition-opacity">
        Crafted with <span className="text-blue-500">Stability</span> & <span className="text-indigo-500">Speed</span>
      </footer>
    </main>
  );
}

export default App;
