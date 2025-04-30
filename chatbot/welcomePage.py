import http.server
import os
import socketserver
import threading


def start_temporary_server(port=8000, max_retries=5) -> tuple[socketserver.ThreadingTCPServer, int]:
    """
    Avvia un server HTTP temporaneo per mostrare una pagina di benvenuto
    mentre il server principale si sta avviando.
    Tenta automaticamente altre porte se quella richiesta è occupata.
    """

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # Imposta la directory principale come la cartella web-client
            web_client_dir = os.path.join(os.path.dirname(__file__), 'web-client')
            super().__init__(*args, directory=web_client_dir, **kwargs)

        def do_GET(self):
            if self.path == '/':
                # Reindirizza alla pagina di benvenuto
                self.path = '/welcome.html'
            elif self.path == '/check-server-status':
                # Risponde con status non pronto
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ready": false}')
                return
            return super().do_GET()

        def log_message(self, format, *args):
            # Disabilita i log del server temporaneo
            pass

    # Classe server personalizzata per permettere il riutilizzo dell'indirizzo
    class ThreadingServerWithReuse(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    # Tenta di avviare il server su porte diverse se quella predefinita è occupata
    current_port = port
    retries = 0

    while retries < max_retries:
        try:
            httpd = ThreadingServerWithReuse(("", current_port), CustomHandler)
            print(f"Server temporaneo avviato sulla porta {current_port}")
            return httpd, current_port
        except OSError as e:
            if e.errno == 48:  # Address already in use
                retries += 1
                current_port = port + retries
                print(f"La porta {current_port - 1} è occupata, provo con la porta {current_port}")
            else:
                raise

    raise OSError(f"Impossibile trovare una porta libera dopo {max_retries} tentativi")


# def run_temp_server(httpd):
#     """Funzione per eseguire il server in un thread separato"""
#     httpd.serve_forever()

temp_httpd = None  # Variabile globale per il server temporaneo


def run_temp_server(port):
    """Funzione per Avviare il server temporaneo di welcome-page thread separato"""
    global temp_httpd
    try:
        temp_httpd, used_port = start_temporary_server(port)
        temp_server_thread = threading.Thread(target=temp_httpd.serve_forever, daemon=True)
        temp_server_thread.start()
        print("Server temporaneo avviato. Caricamento dell'applicazione principale...")

        # Se abbiamo dovuto usare una porta diversa per il server temporaneo, informiamo l'utente
        if used_port != port:
            print(f"NOTA: Il server temporaneo usa la porta {used_port} mentre il server principale userà la porta {port}")
    except Exception as e:
        print(f"Errore nell'avvio del server temporaneo: {e}")
        print("Continuo senza server temporaneo...")
        temp_httpd = None


def stop_temp_server():
    """Ferma il server temporaneo di welcome-page"""
    global temp_httpd
    print("Applicazione principale pronta. Fermo il server temporaneo...")
    if temp_httpd is None:
        print("Nessun server temporaneo in esecuzione.")
        return
    temp_httpd.shutdown()
    temp_httpd.server_close()
    print("Server temporaneo fermato")
