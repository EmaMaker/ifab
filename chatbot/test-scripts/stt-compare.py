#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-

import torch
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

import argparse
import time

import argcomplete
import whisperx
import gc

""" Import local library """
import sys
import os

import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()




# Aggiungi il percorso relativo al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))




if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="WisperX time comparison")
    parser.add_argument("--wav", type=str, required=True, help="Path to the wav file")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    device = "cuda"
    audio_file = args.wav
    batch_size = 16  # reduce if low on GPU mem
    compute_type = "float32"  # change to "int8" if low on GPU mem (may reduce accuracy)

    # delete model if low on GPU resources
    # import gc; gc.collect(); torch.cuda.empty_cache(); del model

    # 1. Transcribe with original whisper (batched)
    start_time_creation = time.time()
    model = whisperx.load_model("large-v3", device, compute_type=compute_type, threads=4) # download_root=model_dir, local_files_only=False
    end_time_creation = time.time()
    time_creation = end_time_creation - start_time_creation
    print(f"Tempo di creazione della classe: {time_creation} secondi")

    # input("Premi Invio per continuare...")

    start_time_first_test = time.time()
    print("Carico un file WAV dalla memoria al modello")
    audio = whisperx.load_audio(audio_file)
    end_time_first_test = time.time()
    time_first_test = end_time_first_test - start_time_first_test
    print(f"Tempo caricamento WAW nel modello: {time_first_test} secondi")

    # input("Premi Invio per continuare...")
    start_time_second_test = time.time()
    print("Ottengo la trascrizione")
    result = model.transcribe(audio, batch_size=batch_size, language="it")
    end_time_second_test = time.time()
    time_second_test = end_time_second_test - start_time_second_test
    print(f"Tempo per generare la stranscrizione: {time_second_test} secondi")

    # input("Premi Invio per continuare...")

    # Esempio di riproduzione di testo
    start_time_genText = time.time()
    print("Mostro il risultato")
    print(result["segments"])  # before alignment
    end_time_genText = time.time()
    time_genText = end_time_genText - start_time_genText
    print(f"Tempo per mostrare la transcrizione: {time_genText} secondi")

    # Calcolo del tempo totale
    total_time = time_creation + time_first_test + time_second_test + time_genText
    print(f"Tempo totale: {total_time} secondi")
    exit(0)
