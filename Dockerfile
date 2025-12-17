# 1. Base Image (Full Python Version)
FROM python:3.9

# 2. Chrome aur Driver Install karein
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Chrome ke Paths set karein
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 4. Folder Set karein
WORKDIR /app

# 5. Git Permission Error Fix
RUN git config --global --add safe.directory '*'

# 6. Requirements Install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Pura Code Copy karein
COPY . .

# 8. Render Start Command (Flask ke liye Gunicorn best hai)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
