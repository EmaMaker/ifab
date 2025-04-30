import http.server
import os
import socketserver
import threading

# Variabile globale per mantenere il riferimento al server
temp_httpd = None

def start_temporary_server(port=8000) -> tuple[socketserver.ThreadingTCPServer, int]:
    """
    Avvia un server HTTP temporaneo per mostrare una pagina di benvenuto
    mentre il server principale si sta avviando.
    Usa esclusivamente la porta specificata.
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

    try:
        httpd = ThreadingServerWithReuse(("", port), CustomHandler)
        print(f"Server temporaneo avviato sulla porta {port}, raggiungibile su http://localhost:{port}")
        return httpd, port
    except OSError as e:
        if e.errno == 48:  # Address already in use
            raise OSError(f"La porta {port} è già in uso. Specificare una porta diversa.")
        else:
            raise


def run_temp_server(port=8000):
    """Funzione per avviare il server temporaneo di welcome-page in un thread separato"""
    global temp_httpd
    try:
        # Verifica se la porta è già in uso
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('localhost', port))
        s.close()

        if result == 0:
            print(f"ATTENZIONE: La porta {port} è già in uso. Continuo senza server temporaneo...")
            return None

        # Avvia il server temporaneo
        httpd, used_port = start_temporary_server(port)
        temp_httpd = httpd

        # Avvia il server in un thread separato
        temp_server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        temp_server_thread.start()
        print("Server temporaneo avviato. Caricamento dell'applicazione principale...")

        return used_port
    except Exception as e:
        print(f"Errore nell'avvio del server temporaneo: {e}")
        print("Continuo senza server temporaneo...")
        temp_httpd = None
        return None


def stop_temp_server():
    """Ferma il server temporaneo di welcome-page"""
    global temp_httpd
    print("Applicazione principale pronta. Fermo il server temporaneo...")
    if temp_httpd is None:
        print("Nessun server temporaneo in esecuzione.")
        return

    try:
        # Chiudi il server principale
        temp_httpd.shutdown()
        temp_httpd.server_close()

        # Se il server ha un socket, prova a chiudere anche quello
        if hasattr(temp_httpd, 'socket'):
            try:
                temp_httpd.socket.close()
            except:
                pass

        temp_httpd = None
        print("Server temporaneo fermato")
    except Exception as e:
        print(f"Errore durante l'arresto del server temporaneo: {e}")
        temp_httpd = None


if __name__ == '__main__':
    # Esegui il server temporaneo per testare la pagina di benvenuto
    run_temp_server(8000)
    try:
        while True:
            pass  # Mantieni il server in esecuzione
    except KeyboardInterrupt:
        stop_temp_server()