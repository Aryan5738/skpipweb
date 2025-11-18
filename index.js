const express = require("express");
const ytsr = require("ytsr");
const ytdl = require("ytdl-core");
const app = express();
const port = 3000;

// Middleware to parse form data
app.use(express.urlencoded({ extended: true }));

// --- YOUTUBE CORE FUNCTIONS ---

/**
 * Searches YouTube using ytsr.
 * @param {string} query Search query.
 * @param {number} limit Number of results.
 * @returns {Array<Object>} Array of video results.
 */
const search = async (query, limit = 5) => {
  const filters = await ytsr.getFilters(query);
  const filter = filters.get('Type').get('Video');
  const searchResults = await ytsr(filter.url, { limit });

  return searchResults.items.map(item => ({
    title: item.title,
    url: item.url,
    id: item.id, // ID is important for ytdl-core
    author: item.author ? item.author.name : 'Unknown',
    views: item.views,
    duration: item.duration,
    uploadedAt: item.uploadedAt,
    thumbnail: item.bestThumbnail.url
  }));
};


/**
 * Generates the download link using ytdl-core.
 * @param {string} url Video URL.
 * @param {string} type 'audio' or 'video'.
 * @param {string} quality Video quality (e.g., '135' for 480p, only relevant for video).
 * @returns {string} The final redirect URL for download/stream.
 */
const getDownloadStreamUrl = async (url, type, quality = '135') => {
  // Get video information (needed to check if video is available and to get formats)
  const info = await ytdl.getInfo(url);

  // Define format filter based on type
  let formatFilter;
  if (type === 'audio') {
    // Highest quality audio only
    formatFilter = 'audioonly';
  } else {
    // Video format matching quality, if available.
    // '135' is typically 480p, '134' is 360p, etc.
    formatFilter = (format) => format.itag == quality && format.container === 'mp4';
  }

  // Get the chosen format object
  const format = ytdl.chooseFormat(info.formats, { 
      filter: formatFilter, 
      quality: type === 'audio' ? 'highestaudio' : quality 
  });

  if (!format) {
      throw new Error(`Requested ${type} format/quality not found for this video.`);
  }

  // ytdl-core returns the direct URL to the media stream
  return format.url;
};


// --- HTML GENERATION FUNCTION (Same as before) ---
function generateHtml(results = null, query = "", error = null) {
    const resultsHtml = results ? results.map(result => `
        <div class="result-item">
            <div class="result-info">
                <img src="${result.thumbnail}" alt="Thumbnail" style="width: 100px; height: auto; margin-right: 15px;">
                <div>
                    <h3>${result.title}</h3>
                    <p>by <strong>${result.author}</strong></p>
                    <p class="views-duration">
                        ${result.views || 'N/A'} | ${result.duration || 'N/A'} | ${result.uploadedAt || 'N/A'}
                    </p>
                </div>
            </div>
            <div class="result-actions">
                <a class="audio-btn" href="/download/audio?url=${encodeURIComponent(result.url)}" target="_blank">
                    Download MP3 (Highest)
                </a>
                <a class="video-btn" href="/download/video?url=${encodeURIComponent(result.url)}&quality=135" target="_blank">
                    Download MP4 (480p)
                </a>
                <a class="video-btn" href="/download/video?url=${encodeURIComponent(result.url)}&quality=134" target="_blank">
                    Download MP4 (360p)
                </a>
            </div>
        </div>
    `).join('') : '';

    // ... (rest of the HTML is the same, just included the result-info style update)

    const noResultsHtml = (results && results.length === 0) ? 
        `<p style="text-align: center; color: orange;">No results found for "${query}". Try a different query.</p>` : '';

    const errorHtml = error ? `<div class="error">${error}</div>` : '';

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader (ytdl-core)</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f9; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        form { display: flex; margin-bottom: 20px; }
        input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; font-size: 16px; }
        button { padding: 10px 15px; background-color: #ff0000; color: white; border: none; border-radius: 0 4px 4px 0; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #cc0000; }
        .error { color: red; text-align: center; margin-bottom: 15px; font-weight: bold; }
        .result-item { border: 1px solid #eee; padding: 15px; margin-bottom: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; background-color: #fafafa; }
        .result-info { flex-grow: 1; display: flex; align-items: center; } /* Updated for thumbnail */
        .result-info h3 { margin-top: 0; color: #06c; }
        .result-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
        .result-actions a { text-decoration: none; padding: 8px 12px; border-radius: 4px; font-size: 14px; transition: background-color 0.3s; }
        .audio-btn { background-color: #4CAF50; color: white; }
        .audio-btn:hover { background-color: #45a049; }
        .video-btn { background-color: #007bff; color: white; }
        .video-btn:hover { background-color: #0056b3; }
        .views-duration { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Song/Video Downloader (ytdl-core)</h1>

        ${errorHtml}

        <form action="/search" method="POST">
            <input type="text" name="query" placeholder="Enter song name or YouTube video title..." value="${query}" required>
            <button type="submit">Search</button>
        </form>

        ${results && results.length > 0 ? `<h2>Search Results for: "${query}"</h2>` : ''}
        <div>
            ${resultsHtml}
            ${noResultsHtml}
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
    res.send(generateHtml(null, query, `An error occurred during search: ${error.message}.`));
  }
});

// Download Route: Uses ytdl-core to get the direct stream URL
app.get("/download/:type", async (req, res) => {
  const { type } = req.params;
  const { url, quality } = req.query; // 'quality' is the itag for video

  if (!url) {
    return res.status(400).send("Video URL is required.");
  }

  try {
    const streamUrl = await getDownloadStreamUrl(url, type, quality);
    
    // Redirect to the stream URL. 
    // The browser will start downloading the file directly from YouTube's server.
    return res.redirect(streamUrl);

  } catch (error) {
    console.error("Download error:", error.message);
    // Show a user-friendly error
    return res.status(500).send(`Error generating download link: ${error.message}. Make sure the URL is correct and the requested quality is available.`);
  }
});

// Start the server
app.listen(port, () => {
  console.log(`YouTube Downloader App listening at http://localhost:${port}`);
});
