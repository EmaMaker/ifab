# -*- coding: utf-8 -*-

import re


def clean_markdown_for_tts(text):
    """
    Rimuove gli elementi di Markdown dal testo per renderlo adatto alla sintesi vocale.
    
    Rimuove:
    - Citazioni (es. [1]: cite:1 "Citation-1")
    - Asterischi per grassetto e corsivo
    - Backtick per il codice
    - Altri elementi di formattazione Markdown
    
    Mantiene:
    - Gli a capo tra elementi di un elenco

    Args:
        text (str): Il testo in formato Markdown da pulire
        
    Returns:
        str: Il testo pulito pronto per essere inviato al TTS
    """
    if not text:
        return text

    # Rimuovi le citazioni nel formato [n]: cite:n "Citation-n"
    text = re.sub(r'\[\d+\]:\s*cite:\d+\s*"[^"]*"', '', text)

    # Rimuovi i riferimenti alle citazioni [n]
    text = re.sub(r'\[\d+\]', '', text)

    # Rimuovi asterischi per grassetto e corsivo (migliorato)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Grassetto
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Corsivo

    # Rimuovi backtick per il codice inline
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Rimuovi blocchi di codice
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Rimuovi formattazione per link [testo](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Rimuovi simboli di intestazione
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Modifica simboli di elenco aggiungendo un punto alla fine di ogni elemento
    text = re.sub(r'^[\*\-\+]\s+(.+?)$', r'\1.', text, flags=re.MULTILINE)

    # Modifica numeri di elenco numerato aggiungendo un punto alla fine di ogni elemento
    text = re.sub(r'^\d+\.\s+(.+?)$', r'\1.', text, flags=re.MULTILINE)

    # Rimuovi linee orizzontali
    text = re.sub(r'^-{3,}|^\*{3,}|^_{3,}', '', text, flags=re.MULTILINE)

    # Rimuovi spazi multipli e tab
    text = re.sub(r'[ \t]+', ' ', text)

    # Rimuovi spazi all'inizio e alla fine di ogni riga
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)

    # Rimuovi newline multipli ma preserva singoli newline per mantenere la struttura del testo
    text = re.sub(r'\n{2,}', '\n', text)

    # Rimuovi spazi prima dei segni di punteggiatura
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)

    # Formatta correttamente il testo per il TTS
    # Prima sostituisci gli a capo con virgole e spazi
    text = re.sub(r'\n', ', ', text)

    # Rimuovi spazi multipli che potrebbero essersi creati durante la pulizia
    text = re.sub(r'[ \t]+', ' ', text)

    # Rimuovi spazi all'inizio e alla fine di ogni riga (mantenendo gli a capo)
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)

    return text.strip()
