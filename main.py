const axios = require("axios");
const ytsearch = require("@neeraj-x0/ytsearch");
const express = require("express");
const app = express();
const port = 3000;

// Middleware to parse form data
app.use(express.urlencoded({ extended: true }));

// --- YOUTUBE CORE FUNCTIONS (Your existing code) ---

const search = async (query, limit = 5) => { // Increased limit for better results
  const filters = await ytsearch.getFilters(query);
  const filter = filters.get("Type").get("Video");
  const options = {
    limit,
  };
  const searchResults = await ytsearch(filter.url, options);
  return searchResults.items.map(
    ({ title, url, author, views, duration, uploadedAt }) => {
      // Adjusted to get author name correctly
      return { title, url, author: author ? author.name : 'Unknown', views, duration, uploadedAt };
    }
  );
};

const ytdlget = async (url) => {
  return new Promise((resolve, reject) => {
    let qu = "query=" + encodeURIComponent(url);

    let config = {
      method: "post",
      maxBodyLength: Infinity,
      url: "https://tomp3.cc/api/ajax/search",
      headers: {
        accept: "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      },
      data: qu,
    };

    axios
      .request(config)
      .then((response) => {
        resolve(response.data);
      })
      .catch((error) => {
        reject(error);
      });
  });
};

function formatYtdata(data, options) {
  const { type, quality } = options;
  const formatted_data = [];

  const processFormat = (format) => {
    if (!format) return; // Skip if format is null/undefined

    const info = {
      vid: data.vid,
      id: format.k,
      size: format.size,
      quality: format.q,
      type: format.f,
    };
    formatted_data.push(info);
  };

  // Ensure mp4, mp3, 3gp links exist before iterating/accessing
  if (data.links && data.links.mp4) Object.values(data.links.mp4).forEach(processFormat);
  if (data.links && data.links.mp3 && data.links.mp3.mp3128) processFormat(data.links.mp3.mp3128);
  if (data.links && data.links["3gp"] && data.links["3gp"]["3gp@144p"]) processFormat(data.links["3gp"]["3gp@144p"]);
  
  let formatted = formatted_data;
  if (type) {
    formatted = formatted_data.filter((format) => format.type === type);
  }
  if (quality) {
    formatted = formatted_data.filter((format) => format.quality === quality);
  }
  return formatted;
}
async function ytdlDl(vid, k) {
  const data = `vid=${vid}&k=${encodeURIComponent(k)}`;

  const config = {
    method: "post",
    maxBodyLength: Infinity,
    url: "https://tomp3.cc/api/ajax/convert",
    headers: {
      accept: "*/*",
      "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    },
    data: data,
  };

  try {
    const response = await axios.request(config);
    return response.data;
  } catch (error) {
    console.error(error);
    throw new Error("An error occurred during the download request");
  }
}

async function yta(url) {
  const data = await ytdlget(url);
  const formatted_data = formatYtdata(data, {
    type: "mp3",
  });
  if (formatted_data.length === 0) {
      throw new Error("MP3 format not found.");
  }
  const k = formatted_data[0].id;
  const vid = formatted_data[0].vid;
  let response = await ytdlDl(vid, k);

  response = {
    ...response,
    sizes: formatted_data[0].size,
    thumb: `https://i.ytimg.com/vi/${vid}/0.jpg`,
  };
  return response;
}

async function ytv(url, quality = "480p") {
  const data = await ytdlget(url);
  const formatted_data = formatYtdata(data, { type: "mp4", quality });
  if (formatted_data.length === 0) {
      throw new Error(`Video format with quality ${quality} not found.`);
  }
  const k = formatted_data[0].id;
  const vid = formatted_data[0].vid;
  let response = await ytdlDl(vid, k);
  response = {
    ...response,
    sizes: formatted_data[0].size,
    thumb: `https://i.ytimg.com/vi/${vid}/0.jpg`,
  };
  return response;
}


// --- HTML GENERATION FUNCTION ---
/**
 * Generates the full HTML string for the page.
 * @param {Array<Object>|null} results Search results array or null.
 * @param {string} query Current search query.
 * @param {string|null} error Error message or null.
 * @returns {string} The full HTML content.
 */
function generateHtml(results = null, query = "", error = null) {
    
    // Function to generate result items HTML
    const resultsHtml = results ? results.map(result => `
        <div class="result-item">
            <div class="result-info">
                <h3>${result.title}</h3>
                <p>by <strong>${result.author}</strong></p>
                <p class="views-duration">
                    ${result.views || 'N/A'} | ${result.duration || 'N/A'} | ${result.uploadedAt || 'N/A'}
                </p>
            </div>
            <div class="result-actions">
                <a class="audio-btn" href="/download/audio?url=${encodeURIComponent(result.url)}" target="_blank">
                    Download MP3
                </a>
                <a class="video-btn" href="/download/video?url=${encodeURIComponent(result.url)}&quality=480p" target="_blank">
                    Download MP4 (480p)
                </a>
            </div>
        </div>
    `).join('') : '';

    // HTML to show if no results were found
    const noResultsHtml = (results && results.length === 0) ? 
        `<p style="text-align: center; color: orange;">No results found for "${query}". Try a different query.</p>` : '';

    // HTML for the error message
    const errorHtml = error ? `<div class="error">${error}</div>` : '';


    // The entire HTML structure as a JavaScript template literal
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Song Downloader (Single-File)</title>
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
        .result-info { flex-grow: 1; }
        .result-info h3 { margin-top: 0; color: #06c; }
        .result-actions { display: flex; gap: 10px; }
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
        <h1>YouTube Song/Video Downloader</h1>

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

// 1. Home Route: Renders the search page
app.get("/", (req, res) => {
  res.send(generateHtml());
});

// 2. Search Route: Handles the search query
app.post("/search", async (req, res) => {
  const { query } = req.body;
  if (!query) {
    return res.send(generateHtml(null, "", "Please enter a search query."));
  }

  try {
    const searchResults = await search(query);
    res.send(generateHtml(searchResults, query, null));
  } catch (error) {
    console.error("Search error:", error);
    res.send(generateHtml(null, query, "An error occurred during search. Try again."));
  }
});

// 3. Download Route: Initiates the download
app.get("/download/:type", async (req, res) => {
  const { type } = req.params;
  const { url, quality } = req.query;

  if (!url) {
    return res.status(400).send("Video URL is required.");
  }

  try {
    let result;
    if (type === "audio") {
      result = await yta(url);
    } else if (type === "video") {
      // Default to 480p if quality is not specified
      result = await ytv(url, quality || "480p");
    } else {
      return res.status(400).send("Invalid download type. Use 'audio' or 'video'.");
    }

    if (result && result.dl_link) {
      // Redirect to the download link to initiate the file download in the browser
      // The content of the file (e.g., MP3/MP4) will be streamed/downloaded from the dl_link.
      return res.redirect(result.dl_link);
    } else {
      return res.status(500).send("Could not retrieve download link.");
    }

  } catch (error) {
    console.error("Download error:", error.message);
    return res.status(500).send(`Error generating download link: ${error.message}`);
  }
});

// Start the server
app.listen(port, () => {
  console.log(`YouTube Downloader App listening at http://localhost:${port}`);
});
