import argparse
import os
import threading
import torch

import whisperx


# Singleton per il modello WhisperX
_whisper_instance = None
_whisper_lock = threading.Lock()


def get_available_gpu():
    """Verifica le GPU disponibili e restituisce l'indice della GPU con più memoria disponibile"""
    if not torch.cuda.is_available():
        return "cpu"
    
    # Ottieni il numero di GPU disponibili
    gpu_count = torch.cuda.device_count()
    if gpu_count == 1:
        return "cuda:0"
    
    # Trova la GPU con più memoria disponibile
    max_free_memory = 0
    best_gpu_idx = 0
    
    for gpu_idx in range(gpu_count):
        # Imposta temporaneamente il dispositivo corrente
        torch.cuda.set_device(gpu_idx)
        # Svuota la cache per ottenere una lettura accurata
        torch.cuda.empty_cache()
        # Ottieni la memoria disponibile
        free_memory = torch.cuda.get_device_properties(gpu_idx).total_memory - torch.cuda.memory_allocated(gpu_idx)
        
        print(f"GPU {gpu_idx}: {free_memory / 1024**3:.2f} GB liberi")
        
        if free_memory > max_free_memory:
            max_free_memory = free_memory
            best_gpu_idx = gpu_idx
    
    return f"cuda:{best_gpu_idx}"


class WhisperListener():
    def __init__(self, model='large-v3', device='auto', compute_type='float32', batch_size=16, language='it', gpu_idx=None):
        global _whisper_instance
        
        self.model = model
        
        # Gestione della selezione della GPU
        if device == 'auto':
            self.device = get_available_gpu()
        elif device == 'cuda' and gpu_idx is not None:
            # Verifica che l'indice GPU specificato sia valido
            if gpu_idx >= 0 and gpu_idx < torch.cuda.device_count():
                self.device = f"cuda:{gpu_idx}"
            else:
                print(f"ATTENZIONE: Indice GPU {gpu_idx} non valido. Utilizzo della GPU con più memoria disponibile.")
                self.device = get_available_gpu()
        else:
            self.device = device
        
        self.compute_type = compute_type  # change to "int8" if low on GPU mem (may reduce accuracy)
        self.batch_size = batch_size  # reduce if low on GPU mem
        self.language = language
        
        # Implementazione del pattern Singleton per evitare ricaricamenti multipli del modello
        with _whisper_lock:
            if _whisper_instance is None:
                print(f"Carico/Scarico il modello '{self.model}' in '{self.device}' con '{self.compute_type}'")
                _whisper_instance = whisperx.load_model(self.model, self.device, compute_type=self.compute_type, threads=4, language=self.language)
                print(f"└─▶ Caricamento del modello completato")
            else:
                print(f"└─▶ Utilizzo modello STT già caricato in memoria")
            
            self.model_obj = _whisper_instance

    def transcribe(self, audio_file) -> dict:
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"File audio '{audio_file}' non trovato")
        audio = whisperx.load_audio(audio_file)
        return self.model_obj.transcribe(audio, batch_size=self.batch_size, language=self.language)

    def transcribeText(self, audio_text) -> dict:
        if not audio_text:
            raise ValueError("Audio text is empty")
        audio = whisperx.load_audio(audio_text)
        result = self.model_obj.transcribe(audio, batch_size=self.batch_size, language=self.language)
        text = ""
        for segment in result["segments"]:
            text += segment["text"] + "\n"
        return text


""" Utility function for Argvparser"""


def whisperListener_argsAdd(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    whisperParser = parser.add_argument_group("WhisperX STT model")
    whisperParser.add_argument("--stt_model", default='large-v3', type=str, help="Whisper model name, if not present is downloaded from huggingface [default '%(default)s']")
    whisperParser.add_argument("--device", type=str, default="auto", help="Device to run the model on (cpu, cuda, or auto) [default '%(default)s']")
    whisperParser.add_argument("--gpu_idx", type=int, default=None, help="Indice specifico della GPU da utilizzare (es. 0, 1) [default: auto]")
    whisperParser.add_argument("--language", type=str, default="it", help="Language of the audio file [default '%(default)s']")
    whisperParser.add_argument("--batch_size", type=int, default=16, help="Batch size for processing [default '%(default)s']")
    whisperParser.add_argument("--compute_type", type=str, default="float32", help="Compute type (float32 or int8) [default '%(default)s']")
    return whisperParser


def whisperListener_useArgs(args: argparse.Namespace) -> WhisperListener:
    wl = WhisperListener(model=args.stt_model, device=args.device, compute_type=args.compute_type, batch_size=args.batch_size, language=args.language, gpu_idx=args.gpu_idx)
    return wl
