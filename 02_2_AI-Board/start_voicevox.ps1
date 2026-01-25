# VOICEVOX Engine Docker Container Startup Script (GPU)
# Requirement: Docker Desktop & NVIDIA GPU

write-host "Starting VOICEVOX Engine (GPU Mode)..."
docker run --rm -it -p 50021:50021 --gpus all voicevox/voicevox_engine:nvidia-ubuntu20.04-latest

# Note: The first run will take time to download the image.
