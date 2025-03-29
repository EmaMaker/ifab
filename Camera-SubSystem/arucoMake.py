import os

import cv2
import numpy as np
import matplotlib.pyplot as plt

# Define the dictionary we want to use
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

os.makedirs('arucoCode/', exist_ok=True)

# Generate a marker
marker_size = 200  # Size in pixels
for marker_id in range(10,40,2):
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

    cv2.imwrite(f'arucoCode/marker_{marker_id}.png', marker_image)
    plt.imshow(marker_image, cmap='gray', interpolation='nearest')
    plt.axis('off')  # Hide axes
    plt.title(f'ArUco Marker {marker_id}')
    plt.show()