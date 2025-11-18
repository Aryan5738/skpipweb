const express = require("express");
const ytsr = require("ytsr");
const ytdl = require("ytdl-core");
const app = express();
const port = 3000;

app.use(express.urlencoded({ extended: true }));

// --- CORE FUNCTIONS ---

const search = async (query, limit = 5) => {
  const filters = await ytsr.getFilters(query);
  const filter = filters.get('Type').get('Video');
  const searchResults = await ytsr(filter.url, { limit });

  return searchResults.items.filter(item => item.type === 'video').map(item => ({
    title: item.title,
    url: item.url,
    id: item.id,
    author: item.author ? item.author.name : 'Unknown',
    views: item.views,
    duration: item.duration,
    uploadedAt: item.uploadedAt,
    thumbnail: item.bestThumbnail ? item.bestThumbnail.url : ''
  }));
};


/**
 * Returns a readable stream for the audio/video.
 * @param {string} url Video URL.
 * @param {string} type 'audio' or 'video'.
 * @param {string} quality Video quality (e.g., '135' for 480p, only relevant for video).
 * @returns {ytdl.ReadableStream} The YTDL stream.
 */
const getStream = (url, type, quality = '135') => {
  let options = {};
  if (type === 'audio') {
    options.filter = 'audioonly';
    options.quality = 'highestaudio';
  } else {
    // For video, we need to choose a format that includes video (itag 135 = 480p mp4)
    options.filter = (format) => format.itag == quality && format.container === 'mp4';
  }

  // Use the built-in ytdl-core download function which returns a stream
  return ytdl(url, options);
};

// --- HTML GENERATION FUNCTION (Modern UI) ---

function generateHtml(results = null, query = "", error = null) {
    
    // Function to generate individual result item HTML
    const resultsHtml = results ? results.map(result => `
        <div class="result-item">
            <div class="result-info">
                <img src="${result.thumbnail}" alt="Thumbnail" class="thumbnail">
                <div class="text-info">
                    <h3>${result.title}</h3>
                    <p class="author">by <strong>${result.author}</strong></p>
                    <p class="stats">
                        ${result.views || 'N/A'} | ${result.duration || 'N/A'} | ${result.uploadedAt || 'N/A'}
                    </p>
                </div>
            </div>
            
            <div class="result-actions">
                <button class="action-btn play-btn" onclick="document.getElementById('audioPlayer').src='/stream/audio?url=${encodeURIComponent(result.url)}'; document.getElementById('audioPlayer').play();">
                    ▶️ Play Audio
                </button>
                <a class="action-btn download-btn" href="/download/audio?url=${encodeURIComponent(result.url)}" download>
                    ⬇️ Download MP3
                </a>
                <a class="action-btn video-btn" href="/download/video?url=${encodeURIComponent(result.url)}&quality=135" download>
                    ⬇️ Download MP4 (480p)
                </a>
            </div>
        </div>
    `).join('') : '';

    const noResultsHtml = (results && results.length === 0) ? 
        `<p class="message-info">No results found for "${query}". Try a different query.</p>` : '';

    const errorHtml = error ? `<div class="message-error">${error}</div>` : '';


    // The entire HTML structure
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader (Modern UI)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #FF0000;
            --secondary-color: #007bff;
            --success-color: #28a745;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #343a40;
        }
        * { box-sizing: border-box; }
        body { 
            font-family: 'Poppins', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: var(--bg-color); 
            color: var(--text-color);
        }
        .container { 
            max-width: 900px; 
            margin: auto; 
            background: var(--card-bg); 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        }
        h1 { text-align: center; color: var(--primary-color); margin-bottom: 25px; font-weight: 600; }
        form { display: flex; margin-bottom: 30px; }
        input[type="text"] { 
            flex-grow: 1; 
            padding: 12px 15px; 
            border: 2px solid #ced4da; 
            border-radius: 8px 0 0 8px; 
            font-size: 16px; 
            transition: border-color 0.3s;
        }
        input[type="text"]:focus { border-color: var(--primary-color); outline: none; }
        button[type="submit"] { 
            padding: 12px 20px; 
            background-color: var(--primary-color); 
            color: white; 
            border: none; 
            border-radius: 0 8px 8px 0; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: 600;
            transition: background-color 0.3s;
        }
        button[type="submit"]:hover { background-color: #cc0000; }
        
        .message-error { color: #dc3545; background-color: #f8d7da; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #f5c6cb; }
        .message-info { color: #6c757d; background-color: #e2e3e5; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #d6d8db; }

        /* Result Item Styles */
        .result-item { 
            border: 1px solid #e9ecef; 
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 10px; 
            display: flex; 
            flex-direction: column; /* Default stack for mobile */
            gap: 15px;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        @media (min-width: 600px) {
            .result-item { flex-direction: row; justify-content: space-between; align-items: center; }
        }
        
        .result-info { display: flex; align-items: center; flex-grow: 1; }
        .thumbnail { width: 100px; height: 60px; object-fit: cover; border-radius: 6px; margin-right: 15px; }
        .text-info h3 { margin: 0 0 5px 0; color: var(--text-color); font-size: 1.1em; line-height: 1.3; }
        .author { font-size: 0.9em; color: #6c757d; margin: 0 0 5px 0; }
        .stats { font-size: 0.8em; color: #adb5bd; margin: 0; }
        
        /* Action Buttons */
        .result-actions { 
            display: flex; 
            gap: 8px; 
            flex-wrap: wrap; 
            justify-content: flex-end;
            margin-top: 10px;
        }
        @media (min-width: 600px) {
            .result-actions { margin-top: 0; }
        }
        
        .action-btn { 
            text-decoration: none; 
            padding: 8px 12px; 
            border-radius: 5px; 
            font-size: 14px; 
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.1s;
        }
        .action-btn:active { transform: scale(0.98); }

        .play-btn { background-color: #ffc107; color: var(--text-color); }
        .play-btn:hover { background-color: #e0a800; }
        .download-btn { background-color: var(--success-color); color: white; }
        .download-btn:hover { background-color: #1e7e34; }
        .video-btn { background-color: var(--secondary-color); color: white; }
        .video-btn:hover { background-color: #0056b3; }

        /* Audio Player */
        #audioPlayerContainer {
            margin-top: 25px;
            padding: 15px;
            background: #f1f1f1;
            border-radius: 8px;
            text-align: center;
        }
        #audioPlayer {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Song & Video Downloader</h1>

        ${errorHtml}

        <form action="/search" method="POST">
            <input type="text" name="query" placeholder="Enter song name or YouTube video title..." value="${query}" required>
            <button type="submit">Search</button>
        </form>

        ${results && results.length > 0 ? `<h2 style="font-size: 1.4em; border-bottom: 2px solid #eee; padding-bottom: 10px;">Results for: "${query}"</h2>` : ''}
        <div>
            ${resultsHtml}
            ${noResultsHtml}
        </div>

        <div id="audioPlayerContainer">
            <p style="margin: 0 0 10px 0;">Audio Player (Press 'Play Audio' on a result to stream)</p>
            <audio controls id="audioPlayer" type="audio/mpeg"></audio>
        </div>

    </div>
</body>
</html>
    `;
}

// --- EXPRESS ROUTES ---

app.get("/", (req, res) => {
  res.send(generateHtml());
});

app.post("/search", async (req, res) => {
  const { query } = req.body;
  if (!query) {
    return res.send(generateHtml(null, "", "Please enter a search query."));
  }

  try {
    const searchResults = await search(query);
    res.send(generateHtml(searchResults, query, null));
  } catch (error) {
    console.error("Search error:", error.message);
    res.send(generateHtml(null, query, `Search failed. Reason: ${error.message}.`));
  }
});

// 1. /STREAM Route (For inline Playback)
app.get("/stream/:type", async (req, res) => {
  const { type } = req.params;
  const { url, quality } = req.query; 

  if (!url) return res.status(400).send("Video URL is required.");

  try {
    const stream = getStream(url, type, quality);
    
    // Set appropriate headers for streaming
    res.set('Content-Type', type === 'audio' ? 'audio/mpeg' : 'video/mp4');
    res.set('Content-Disposition', 'inline'); 

    // Pipe the YTDL stream directly to the Express response
    stream.pipe(res);

  } catch (error) {
    console.error("Stream error:", error.message);
    res.status(500).send(`Streaming error: ${error.message}. Please check video availability.`);
  }
});

// 2. /DOWNLOAD Route (For File Saving)
app.get("/download/:type", async (req, res) => {
    const { type } = req.params;
    const { url, quality } = req.query; 
    
    if (!url) return res.status(400).send("Video URL is required.");

    try {
        const stream = getStream(url, type, quality);

        // Set headers to force download
        const ext = type === 'audio' ? 'mp3' : 'mp4';
        res.set('Content-Type', type === 'audio' ? 'audio/mpeg' : 'video/mp4');
        res.set('Content-Disposition', `attachment; filename="youtube_download.${ext}"`);
        
        // Pipe the stream to the response
        stream.pipe(res);

    } catch (error) {
        console.error("Download error:", error.message);
        res.status(500).send(`Download error: ${error.message}. Make sure the URL is correct and the requested quality is available.`);
    }
});


// Start the server
app.listen(port, () => {
  console.log(`YouTube Downloader App listening at http://localhost:${port}`);
});
