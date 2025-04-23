import json
import socket

from vision.vision import Vision

CLIENT_1 = "10.42.0.200"
CLIENT_PORT = 4242

# Memoria per i dati più recenti
memory = {
    'robot': {'data': None, 'valid': False},
    'markers': {}
}

# Variabile per tenere traccia della socket
sock = None

def get_socket():
    """Ottiene una socket valida o ne crea una nuova."""
    global sock
    if sock is None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"Errore nella creazione della socket: {e}")
    return sock

targetMachina = "3d"

def send_to_robot(data: dict):
    """Invia dati al robot, utilizzando la memoria per completare il pacchetto."""
    global memory

    # Invalida il robot se non ci sono nuovi dati
    if data.get('robot') is not None:
        memory['robot']['data'] = data['robot']
        memory['robot']['valid'] = True
    else:
        # Quando arrivano nuovi dati ma senza informazioni sul robot, lo invalidiamo
        memory['robot']['valid'] = False

    # Aggiorna la memoria dei marker
    for marker_key, marker_data in data.get('markers', {}).items():
        memory['markers'][marker_key] = marker_data

    # Componi il pacchetto da inviare
    toSend = {}
    if memory['robot']['valid'] and memory['robot']['data'] is not None:
        toSend['robot'] = {
            "x": memory['robot']['data']["position"][0],
            "y": memory['robot']['data']["position"][1],
            'theta': memory['robot']['data']["angle"]
        }

    if memory['markers'].get(targetMachina) is not None:
        toSend['target'] = {
            "x": memory['markers'][targetMachina]["position"][0],
            "y": memory['markers'][targetMachina]["position"][1],
            'theta': memory['markers'][targetMachina]["angle"]
        }

    print("Data receve from Camera:", data)
    print('Data Send to robot:', toSend)

    # Invia i dati usando la socket solo se c'è qualcosa da inviare
    if toSend:
        try:
            s = get_socket()
            if s:
                json_data = json.dumps(toSend, indent=0).replace("\n", "")
                bytes_data = json_data.encode('utf-8')  + b'\0'
                s.sendto(bytes_data, (CLIENT_1, CLIENT_PORT))
        except Exception as e:
            print(f"Errore nell'invio dei dati: {e}")
            # Resetta la socket in caso di errore
            global sock
            sock = None


# Example usage
if __name__ == '__main__':
    with open('config.json') as f:
        d = json.load(f)
        corners_ids = [
            d['table']['aruco']['top-left'], d['table']['aruco']['top-right'],
            d['table']['aruco']['bottom-right'], d['table']['aruco']['bottom-left']]
        tableSize = (d['table']['width'], d['table']['height'])
        # corners_ids = [0, 1, 2, 3]
        transformer = Vision(camera_index=d["cameraIndex"], marker_corners_ids=corners_ids,
                             width=d['table']['width'], height=d['table']['height'],
                             robot=d['robot'], macchinari=d['macchinari'],
                             sendToRobot=send_to_robot,
                             display=True)
        transformer.run()
