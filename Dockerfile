# 1. Base Image
FROM python:3.9

# 2. Chrome & Dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Environment Variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 4. Work Directory
WORKDIR /app

# 5. Copy Files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 6. Make start.sh executable (Important)
RUN chmod +x start.sh

# 7. Start Command (Ab hum script use karenge)
CMD ["./start.sh"]
