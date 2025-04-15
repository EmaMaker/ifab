# -*- coding: utf-8 -*-

import argparse
import os
import queue
import threading
import wave

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

# Singleton per il modello TTS
_tts_instance = None
_tts_lock = threading.Lock()


class AudioPlayer:
    def __init__(self, voice_model_path):
        global _tts_instance
        
        # Implementazione del pattern Singleton per evitare ricaricamenti multipli del modello TTS
        with _tts_lock:
            if _tts_instance is None:
                print(f"Caricamento del modello TTS da: {voice_model_path}")
                _tts_instance = PiperVoice.load(voice_model_path)
                print("└─▶ Modello TTS caricato con successo")
            else:
                print("└─▶ Utilizzo modello TTS già caricato in memoria")
                
            self.voice = _tts_instance
            
        self.stream = None
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._play_audio)
        self.thread.daemon = True
        self.thread.start()
        self.dType = np.int16
        self.blockItemSize = 4096
        self.silence_sound = np.zeros(int(self.voice.config.sample_rate * 0.3), dtype=self.dType)

    def _ensure_stream_open(self):
        if self.stream is None or not self.stream.active:
            self.stream = sd.OutputStream(
                samplerate=self.voice.config.sample_rate,
                channels=1,
                dtype=self.dType,
                blocksize=self.blockItemSize,
                latency='low'
            )
            self.stream.start()

    def _play_audio(self):
        while True:
            audio_data = self.queue.get()
            if audio_data is None:
                break
            self._ensure_stream_open()
            self.stream.write(audio_data)
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play_wav_from_memory(self, wav_data):
        index = 0
        toSend = len(wav_data) - 1 // np.dtype(self.dType).itemsize
        while toSend > 0:
            int_data = np.frombuffer(wav_data, dtype=np.int16, count=min(self.blockItemSize, toSend // np.dtype(self.dType).itemsize), offset=index)
            self.queue.put(int_data)
            index += self.blockItemSize * np.dtype(self.dType).itemsize
            toSend -= self.blockItemSize * np.dtype(self.dType).itemsize

    def play_text(self, text):
        for audio_bytes in self.voice.synthesize_stream_raw(text):
            int_data = np.frombuffer(audio_bytes, dtype=np.int16)
            self.queue.put(int_data)

    def is_playing(self):
        return self.stream is not None and self.stream.active

    def waitEndBuffer(self):
        self.queue.put(self.silence_sound)
        self.queue.put(None)
        self.thread.join()
        self.thread = threading.Thread(target=self._play_audio)
        self.thread.daemon = True
        self.thread.start()


def open_wave(wave_file):
    with wave.open(wave_file, 'rb') as wf:
        wav_data = wf.readframes(wf.getnframes())
    return wav_data


""" Utility function for Argvparser"""


def audioPlayer_argsAdd(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    audioPlayerParser = parser.add_argument_group("Audio Player for TTS")
    audioLibPath = os.path.join(os.path.dirname(__file__))
    audioPlayerParser.add_argument("--tts_model", type=str, help="Path to the Piper-TTS voice model '*.onnx' [default '%(default)s']",
                        default=os.path.relpath(os.path.join(audioLibPath, "../tts-model", "it_IT-paola-medium.onnx")))
    return audioPlayerParser


def audioPlayer_useArgs(args: argparse.Namespace) -> AudioPlayer:
    player = AudioPlayer(args.tts_model)
    return player
