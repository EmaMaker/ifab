#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-

import torch

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

import argparse
import time

import argcomplete

""" Import local library """
import sys
import os

import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

# Aggiungi il percorso relativo al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import chatLib.WhisperListener as wl

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="WisperX time comparison")
    wl.whisperListener_argsAdd(parser)
    parser.add_argument("--wav", type=str, required=True, help="Path to the audio file")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # 1. Transcribe with original whisper (batched)
    start_time_creation = time.time()
    listener, ready_event = wl.whisperListener_useArgs(args)
    if wl.wait_for_model_loading(ready_event):
        print("Modello whisper caricato con successo")
    else:
        print("Timeout durante il caricamento del modello whisper")
    end_time_creation = time.time()
    time_creation = end_time_creation - start_time_creation
    print(f"Tempo di creazione della classe: {time_creation} secondi")

    start_time_first_test = time.time()
    print("Carico un file WAV dalla memoria al modello e lo trascrivo")
    result = listener(args.wav)
    end_time_first_test = time.time()
    time_first_test = end_time_first_test - start_time_first_test
    print(f"Tempo caricamento e processamento del file  WAW nel modello: {time_first_test} secondi")

    print("Mostro il risultato")
    print(result)  # before alignment

    # Calcolo del tempo totale
    total_time = time_creation + time_first_test
    print(f"Tempo totale: {total_time} secondi")
    exit(0)
