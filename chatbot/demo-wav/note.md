└─▶ $ pip install whisperx 
# In base all'os installa:
install ffmpeg cuDNN nvtop nvidia-drivers

# Esempi da lanciare dalla home del repo
whisperx --model small --language it chatbot/temp/audio_20250411-131426.wav --compute_type float32

whisperx --model large-v3 --compute_type float32 --language it chatbot/temp/audio_20250411-131426.wav 
