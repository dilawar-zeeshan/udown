const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const app = express();
const port = 7860;

app.use(cors());
app.use(express.json());

// Health Check
app.get('/', (req, res) => {
    res.json({ status: 'ok', message: 'Downloader Service is active on Local IP', time: new Date().toISOString() });
});

// Endpoint: /video-info
app.post('/video-info', (req, res) => {
    let { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL is required' });
    if (!url.startsWith('http')) url = 'https://' + url;

    // Local machines usually don't need complex DNS monkeypatching
    // We use common extractor args to skip age gates/bot checks
    const args = [
        '--no-playlist',
        '--no-cache-dir',
        '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '--extractor-args', 'youtube:player_client=android,ios',
        '-J', 
        url
    ];

    const process = spawn('yt-dlp', args);

    let output = '';
    let errorOutput = '';

    process.stdout.on('data', (data) => output += data.toString());
    process.stderr.on('data', (data) => errorOutput += data.toString());

    process.on('close', (code) => {
        if (code !== 0) {
            console.error('yt-dlp error:', errorOutput);
            return res.status(500).json({ error: 'Failed', details: errorOutput });
        }

        try {
            const data = JSON.parse(output);
            const formats = (data.formats || [])
                .filter(f => f.vcodec !== 'none' && (f.ext === 'mp4' || f.container === 'mp4'))
                .map(f => ({
                    format_id: f.format_id,
                    quality: f.format_note || f.resolution || 'unknown',
                    ext: f.ext,
                    filesize: f.filesize || f.filesize_approx,
                    url: f.url
                }));

            res.json({
                title: data.title,
                thumbnail: data.thumbnail,
                duration: data.duration,
                formats: formats
            });
        } catch (e) {
            res.status(500).json({ error: 'Parse Error' });
        }
    });
});

// Endpoint: /download
app.get('/download', (req, res) => {
    let { url, format_id } = req.query;
    if (!url || !format_id) return res.status(400).json({ error: 'Required fields missing' });
    if (!url.startsWith('http')) url = 'https://' + url;

    res.setHeader('Content-Disposition', `attachment; filename="video.mp4"`);
    res.setHeader('Content-Type', 'video/mp4');

    const args = [
        '--no-playlist',
        '--no-cache-dir',
        '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '--extractor-args', 'youtube:player_client=android,ios',
        '-f', format_id,
        '-o', '-',
        url
    ];

    const downloader = spawn('yt-dlp', args);
    downloader.stdout.pipe(res);
    downloader.on('close', () => res.end());
    req.on('close', () => downloader.kill());
});

app.listen(port, "0.0.0.0", () => {
    console.log(`Downloader service listening at http://localhost:${port}`);
    console.log(`Use Cloudflared to expose this port to the internet.`);
});
