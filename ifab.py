import json
import socket

from vision.vision import Vision

CLIENT_1 = "ifab.local"
CLIENT_PORT = 4242
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

targetMachina = "3d"


def send_to_robot(data: dict):
    # Placeholder function to send data to the robot
    print("Sending data to robot:", data)

    toSend = {}
    if data.get('robot') is not None:
        toSend['robot'] = {
            "x": data['robot']["position"][0],
            "y": data['robot']["position"][1],
            'theta': data['robot']["angle"]
        }
    if data['markers'].get('targetMachina') is not None:
        toSend['target'] = {
            "x": data['markers']['targetMachina']["position"][0],
            "y": data['markers']['targetMachina']["position"][1],
            'theta': data['markers']['targetMachina']["angle"]}
    print('toSent', toSend)
    json_data = json.dumps(data, indent=0).replace("\n", "")
    bytes_data = json_data.encode('utf-8')
    # sock.sendto(bytes_data, (CLIENT_1, CLIENT_PORT))


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
