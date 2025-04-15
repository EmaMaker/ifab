└─▶ $ pip install whisperx
install ffmpeg  
sudo apt install nvidia-cudnn nvtop
fix for invidia missing driver: https://github.com/m-bain/whisperX/issues/902

export LD_LIBRARY_PATH="/home/alfy/Documents/02_myRepo/ifab-chatbot/.venv/lib/python3.10/site-packages/nvidia/cudnn/lib"

whisperx --model large-v3 --language it chatbot/demo-wav/audio_20250411-143626.wav --compute_type float32 