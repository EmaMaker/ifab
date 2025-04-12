#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-


import argparse
import time

import argcomplete

""" Import local library """
import sys
import os

# Aggiungi il percorso relativo al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from pyLib import AudioPlayer as ap

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Piper-TTS time comparison")
    parser.add_argument("--model", type=str, required=True, help="Path to the Piper-TTS model")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    model_dir = os.path.dirname(args.model)

    # Inizio del test di creazione della classe
    start_time_creation = time.time()
    player = ap.AudioPlayer(args.model)
    end_time_creation = time.time()
    time_creation = end_time_creation - start_time_creation
    print(f"Tempo di creazione della classe: {time_creation} secondi")

    input("Premi Invio per continuare...")

    # Inizio della prima prova
    start_time_first_test = time.time()
    print("Riproduzione di un file WAV dalla memoria")
    wav_data = ap.open_wave(os.path.join(model_dir, "welcome.wav"))
    player.play_wav_from_memory(wav_data)
    # Fine della prima prova
    player.waitEndBuffer()
    end_time_first_test = time.time()
    time_first_test = end_time_first_test - start_time_first_test
    print(f"Tempo della prima prova: {time_first_test} secondi")

    # Inizio della seconda prova
    input("Premi Invio per continuare...")
    start_time_second_test = time.time()
    print("Ripeto con il wave già in ram")
    player.play_wav_from_memory(wav_data)
    player.waitEndBuffer()

    # Fine della seconda prova
    end_time_second_test = time.time()
    time_second_test = end_time_second_test - start_time_second_test
    print(f"Tempo della seconda prova: {time_second_test} secondi")

    input("Premi Invio per continuare...")

    start_time_genText = time.time()
    # Esempio di riproduzione di testo
    player.play_text("Connessione in corso.")
    player.waitEndBuffer()
    end_time_genText = time.time()
    time_genText = end_time_genText - start_time_genText
    print(f"Tempo generazione e riproduzione test: {time_genText} secondi")

    # Calcolo del tempo totale
    total_time = time_creation + time_first_test + time_second_test + time_genText
    print(f"Tempo totale: {total_time} secondi")
    exit(0)
