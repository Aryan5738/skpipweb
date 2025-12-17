#!/bin/bash

# 1. 1.5 GB Swap File banayein (RAM badhane ke liye)
echo "Creating Swap File..."
fallocate -l 1.5G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "Swap Created!"

# 2. App Start karein
exec gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300
