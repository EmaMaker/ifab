import argparse
import atexit
import multiprocessing
import os
import uuid
from typing import Callable

import torch


# Sposta funzioni al livello principale del modulo
def get_available_gpu() -> tuple[str, int]:
    """Verifica le GPU disponibili e restituisce l'indice della GPU con più memoria disponibile"""
    if not torch.cuda.is_available():
        print("ATTENZIONE: GPU non disponibile, utilizzo CPU")
        return "cpu", 0

    # Ottieni il numero di GPU disponibili
    gpu_count = torch.cuda.device_count()
    if gpu_count == 1:
        print("ATTENZIONE: Solo una GPU disponibile, utilizzo GPU 0")
        return "cuda", 0

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

        print(f"GPU {gpu_idx}: {free_memory / 1024 ** 3:.2f} GB liberi")

        if free_memory > max_free_memory:
            max_free_memory = free_memory
            best_gpu_idx = gpu_idx

    return "cuda", best_gpu_idx


class WhisperListener:
    def __init__(self, model='large-v3', device='auto', compute_type='float32', batch_size=16, language='it', gpu_idx=None):
        import whisperx

        self.model = model

        # Gestione della selezione della GPU
        if device == 'auto':
            self.device, self.gpu_idx = get_available_gpu()
        elif device == 'cuda' and gpu_idx is not None:
            # Verifica che l'indice GPU specificato sia valido
            if 0 <= gpu_idx < torch.cuda.device_count():
                self.device = "cuda"
                self.gpu_idx = gpu_idx
            else:
                print(f"ATTENZIONE: Indice GPU {gpu_idx} non valido. Utilizzo della GPU con più memoria disponibile.")
                self.device, self.gpu_idx = get_available_gpu()
        elif device == 'cpu':
            # Per la CPU, device_index deve essere sempre 0
            self.device = device
            self.gpu_idx = 0
        else:
            self.device = device
            self.gpu_idx = gpu_idx

        self.compute_type = compute_type  # change to "int8" if low on GPU mem (may reduce accuracy)
        self.batch_size = batch_size  # reduce if low on GPU mem
        self.language = language

        print(f"Carico/Scarico il modello '{self.model}' in '{self.device}' con '{self.compute_type}'")
        self.model_obj = whisperx.load_model(self.model, self.device, self.gpu_idx, compute_type=self.compute_type, threads=4, language=self.language)
        print(f"└─▶ Caricamento del modello completato")

    def transcribe(self, audio_file) -> dict:
        import whisperx
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"File audio '{audio_file}' non trovato")
        audio = whisperx.load_audio(audio_file)
        return self.model_obj.transcribe(audio, batch_size=self.batch_size, language=self.language)

    def transcribeText(self, audio_text) -> str:
        import whisperx
        if not audio_text:
            raise ValueError("Audio text is empty")
        audio = whisperx.load_audio(audio_text)
        result = self.model_obj.transcribe(audio, batch_size=self.batch_size, language=self.language)
        text = ""
        for segment in result["segments"]:
            text += segment["text"] + "\n"
        return text


# Funzioni separate per il multiprocessing
def wisperx_process_worker(input_queue, response_dict, condition, ready_event, model, device, compute_type, batch_size, language, gpu_idx):
    """Funzione per il processo figlio che esegue l'analisi del file audio"""
    try:
        # Creiamo l'oggetto WhisperListener qui dentro il processo
        wL = WhisperListener(model=model, device=device, compute_type=compute_type,
                             batch_size=batch_size, language=language, gpu_idx=gpu_idx)
        # Segnala che il modello è stato caricato con successo
        ready_event.set()

        while True:
            request = input_queue.get()
            if request is None:
                break
            file_path, request_id = request
            result = wL.transcribeText(file_path)
            with condition:
                response_dict[request_id] = result
                condition.notify_all()
    except Exception as e:
        # In caso di errore, imposta l'errore nel dizionario condiviso e segnala l'evento
        with condition:
            response_dict["__error__"] = str(e)
            ready_event.set()
            condition.notify_all()


def thread_function(input_queue, response_dict, condition, file_path) -> str:
    """Funzione per gestire la comunicazione tra il processo principale e il processo figlio"""
    request_id = str(uuid.uuid4())  # Converti UUID a stringa per sicurezza
    input_queue.put((file_path, request_id))
    with condition:
        condition.wait_for(lambda: request_id in response_dict)
    return response_dict.pop(request_id)


def wisperx_process_worker(input_queue, response_dict, condition, ready_event, model, device, compute_type, batch_size, language, gpu_idx):
    """Funzione per il processo figlio che esegue l'analisi del file audio"""
    try:
        # Creiamo l'oggetto WhisperListener qui dentro il processo
        wL = WhisperListener(model=model, device=device, compute_type=compute_type,
                             batch_size=batch_size, language=language, gpu_idx=gpu_idx)
        # Segnala che il modello è stato caricato con successo
        ready_event.set()

        while True:
            request = input_queue.get()
            if request is None:
                break
            file_path, request_id = request
            result = wL.transcribeText(file_path)
            with condition:
                response_dict[request_id] = result
                condition.notify_all()
    except Exception as e:
        # In caso di errore, imposta l'errore nel dizionario condiviso e segnala l'evento
        with condition:
            response_dict["__error__"] = str(e)
            ready_event.set()
            condition.notify_all()


def whisperX_spawn_process(model='large-v3', device='auto', compute_type='float32',
                           batch_size=16, language='it', gpu_idx=None) -> tuple[Callable[[str], str], multiprocessing.Event]:
    """
    Funzione per spawnare un processo figlio che instanzi whisperX in un processo python differente.
    see: https://github.com/m-bain/whisperX/issues/1124
    """
    # Crea un manager per la comunicazione tra processi
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    response_dict = manager.dict()
    condition = manager.Condition()
    ready_event = manager.Event()  # Evento per segnalare quando il modello è pronto

    # Crea e avvia il processo
    process = multiprocessing.Process(
        target=wisperx_process_worker,
        args=(input_queue, response_dict, condition, ready_event, model, device,
              compute_type, batch_size, language, gpu_idx)
    )
    process.daemon = True  # Assicura che il processo figlio termini quando il processo padre termina
    process.start()

    # Funzione per terminare il processo in modo pulito
    def terminate_process():
        try:
            # Invia un segnale None per terminare il ciclo nel worker
            input_queue.put(None)
            # Attendi che il processo termini (con timeout)
            process.join(timeout=2)
            # Se il processo è ancora in esecuzione dopo il timeout, terminalo forzatamente
            if process.is_alive():
                process.terminate()
                process.join(timeout=1)
        except Exception as e:
            print(f"Errore durante la terminazione del processo whisperX: {e}")
            # In caso di errori durante la chiusura, forza la terminazione
            if process.is_alive():
                try:
                    process.terminate()
                except:
                    pass

    # Registra la funzione di terminazione con atexit per chiamarla automaticamente all'uscita
    atexit.register(terminate_process)

    # Crea una closure per inviare richieste al processo
    def send_request(path):
        return thread_function(input_queue, response_dict, condition, path)

    return send_request, ready_event


def wait_for_model_loading(ready_event, timeout=300):
    """
    Attende che il modello sia caricato completamente.

    Args:
        ready_event: Evento che sarà impostato quando il modello è pronto
        timeout: Tempo massimo di attesa in secondi

    Returns:
        bool: True se il modello è stato caricato con successo, False in caso di timeout
    """
    return ready_event.wait(timeout=timeout)


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


def whisperListener_useArgs(args: argparse.Namespace):
    """
    Crea un worker per WhisperX utilizzando gli argomenti forniti.

    Returns:
        tuple: (send_func, ready_event)
               - send_func: Funzione per inviare richieste di trascrizione
               - ready_event: Evento che sarà impostato quando il modello è pronto
    """
    send_func, ready_event = whisperX_spawn_process(
        model=args.stt_model, device=args.device, compute_type=args.compute_type,
        gpu_idx=args.gpu_idx, batch_size=args.batch_size, language=args.language
    )
    return send_func, ready_event
