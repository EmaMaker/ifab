import os

import cv2
import matplotlib.pyplot as plt

if __name__ == '__main__':

    # Define the dictionary we want to use
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    os.makedirs('arucoCode/', exist_ok=True)

    # Generate a marker
    marker_size = 200  # Size in pixels
    ids = [10, 12, 14, 16, 18, 100, 110, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240]
    for marker_id in ids:
        marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

        cv2.imwrite(f'arucoCode/marker_{marker_id}.png', marker_image)
        plt.imshow(marker_image, cmap='gray', interpolation='nearest')
        plt.axis('off')  # Hide axes
        plt.title(f'ArUco Marker {marker_id}')
        plt.show()
