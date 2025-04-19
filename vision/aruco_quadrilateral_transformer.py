import json
from typing import Callable

import cv2
import numpy as np

from quadrilateral_transformer import QuadrilateralTransformer

# TODO: Ripulirlo dall'edge detection

class ArUcoQuadrilateralTransformer(QuadrilateralTransformer):

    # La funzione sendToRobot riceve un dizionario con tutte le chiavi che sono stati identificati, e per ogniuno di loro x,y,thetaRad,
    # poi si occupa lui di inviare il messaggio al robot

    # Macchinari contiene un dizionatio con le key del macchinario e l'aruco corrispondente + offset

    def __init__(self, camera_index=0, aruco_dict_type=cv2.aruco.DICT_6X6_250,
                 marker_corners_ids=[10, 12, 14, 16], min_area=1000, output_size=(800, 600),
                 width_cm=30, height_cm=30,
                 robot: dict = {"aruco": 18, "x_offset": 2, "y_offset": 0, "theta_offset": 0},
                 macchinari: dict = {"3d": {"aruco": 20, "x_offset": 30, "y_offset": 30, "theta_offset": 0},
                                     "laser": {"aruco": 21, "x_offset": 0, "y_offset": 0, "theta_offset": 0}},
                 sendToRobot: Callable[[dict], None] = None):
        # Initialize parent class with default parameters
        super().__init__(camera_index, min_area=min_area, output_size=output_size)

        # ArUco specific parameters
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        # Expected marker IDs for the four corners
        # Order should be: top-left, top-right, bottom-right, bottom-left
        self.marker_corners_ids = marker_corners_ids

        # Window name override
        self.window_name = 'ArUco Quadrilateral Transformer'

        # Physical dimensions in cm
        self.width_cm = width_cm
        self.height_cm = height_cm
        # Scale factors to convert from pixels to cm
        self.scale_x = width_cm / output_size[0]
        self.scale_y = height_cm / output_size[1]

        # Salva stato dell'id Robot
        self.robot = robot
        self.macchinari = macchinari
        self.macchinari_id = {} # Inizializza un dizionario vuoto per memorizzare il mapping degli id aruco e key dei macchinari
        for key, mData in macchinari.items():
            self.macchinari_id[mData["aruco"]] = key

        self.sendToRobot = sendToRobot

    def find_quadrilateral(self, frame, display=True):
        # Convert to grayscale for ArUco detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers
        corners, ids, rejected = self.detector.detectMarkers(gray)

        # If no markers detected, return None
        if ids is None:
            return None

        # Initialize array to store the four corner points
        quad_corners = np.zeros((4, 2), dtype=np.float32)
        found_markers = 0

        # Map detected markers to their expected positions
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in self.marker_corners_ids:
                # Get the index of this marker in our expected list
                idx = self.marker_corners_ids.index(marker_id)

                # Get the center of the marker
                marker_corners = corners[i][0]
                center_x = np.mean(marker_corners[:, 0])
                center_y = np.mean(marker_corners[:, 1])

                # Store the center point
                quad_corners[idx] = [center_x, center_y]
                found_markers += 1

        # Only draw and display if display flag is True
        if display:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # Draw the quadrilateral
            for i in range(min(4, found_markers)):
                pt1 = tuple(quad_corners[i].astype(int))
                pt2 = tuple(quad_corners[(i + 1) % 4].astype(int))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            # Display the frame with markers
            cv2.imshow(self.window_name, frame)

        # If we didn't find all four markers, return None
        if found_markers < 4:
            return None
        return quad_corners

    def process_frame(self, frame, display=True):
        # Find quadrilateral using ArUco markers
        corners = self.find_quadrilateral(frame, display=display)

        # Convert to grayscale for ArUco detection (for all markers)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect all ArUco markers in the frame
        all_corners, all_ids, rejected = self.detector.detectMarkers(gray)

        # Update corners if found, otherwise use last good corners
        if corners is not None:
            # Update the last good corners when a valid quadrilateral is found
            self.last_good_corners = corners

        # Use the last good corners if available, otherwise use blank frame
        if self.last_good_corners is not None:
            # Transform the perspective using last good corners
            warped = self.transform_perspective(frame, self.last_good_corners)

            # Process internal markers if any markers were detected
            if all_ids is not None and len(all_ids) > 0:
                # Get the perspective transform matrix
                src_pts = self.order_points(self.last_good_corners.astype(np.float32))
                dst_pts = np.array([
                    [0, 0],
                    [self.output_size[0] - 1, 0],
                    [self.output_size[0] - 1, self.output_size[1] - 1],
                    [0, self.output_size[1] - 1]
                ], dtype=np.float32)
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

                # Find markers that are not corner markers
                internal_markers = []
                for i, marker_id in enumerate(all_ids.flatten()):
                    if marker_id not in self.marker_corners_ids:  # Do only if Aruco is different form Rectangle corners
                        marker_corners = all_corners[i][0]

                        # Calculate center of the marker
                        center_x = np.mean(marker_corners[:, 0])
                        center_y = np.mean(marker_corners[:, 1])
                        marker_center = np.array([center_x, center_y, 1.0])

                        # Transform the center point to the warped coordinate system
                        transformed_center = np.matmul(matrix, marker_center)
                        transformed_x = transformed_center[0] / transformed_center[2]
                        transformed_y = transformed_center[1] / transformed_center[2]

                        # Convert pixel coordinates to cm from top-left
                        # TODO: Verificare se tra le info passate nel config ci sia un offset per la posizione da aggiungere, 2cm avanti rispetto l'asse (forse x da vedere, offset 2;0 cm)
                        pos_x_cm = transformed_x * self.scale_x
                        pos_y_cm = transformed_y * self.scale_y

                        # Calculate the orientation angle of the marker
                        # ArUco markers have a specific orientation - the first corner is the top-right
                        # Calculate vectors for two adjacent sides of the marker
                        v1 = marker_corners[1] - marker_corners[0]  # Vector from top-right to bottom-right
                        v2 = marker_corners[3] - marker_corners[0]  # Vector from top-right to top-left

                        # Use the direction of v1 (top-right to bottom-right) for angle calculation
                        # TODO: Verificare se tra le info passate nel config ci sia un offset per l'angolo da aggiungere
                        angle_rad = np.arctan2(v1[1], v1[0])
                        angle_deg = np.degrees(angle_rad)

                        # Transform two points along the direction vector to see how the angle transforms
                        p1 = np.array([center_x, center_y, 1.0])
                        p2 = np.array([center_x + np.cos(angle_rad) * 20, center_y + np.sin(angle_rad) * 20, 1.0])

                        # Transform both points
                        tp1 = np.matmul(matrix, p1)
                        tp2 = np.matmul(matrix, p2)

                        # Normalize the transformed points
                        tp1 = tp1 / tp1[2]
                        tp2 = tp2 / tp2[2]

                        # Calculate the transformed angle
                        transformed_angle_rad = np.arctan2(tp2[1] - tp1[1], tp2[0] - tp1[0])
                        transformed_angle_deg = np.degrees(transformed_angle_rad)

                        # Store the marker information
                        internal_markers.append({
                            'id': marker_id,
                            'position': (pos_x_cm, pos_y_cm),
                            'position_px': (transformed_x, transformed_y),
                            'angle': transformed_angle_deg
                        })

                        # Draw the marker position and information on the warped image
                        # Draw a circle at the marker center
                        cv2.circle(warped, (int(transformed_x), int(transformed_y)), 5, (0, 0, 255), -1)

                        # Draw a line indicating the orientation
                        line_length = 30
                        end_x = int(transformed_x + line_length * np.cos(transformed_angle_rad))
                        end_y = int(transformed_y + line_length * np.sin(transformed_angle_rad))
                        cv2.line(warped, (int(transformed_x), int(transformed_y)), (end_x, end_y), (0, 255, 0), 2)

                        # Add text with marker information
                        pos_text = f"ID: {marker_id}, Pos: ({pos_x_cm:.1f}cm, {pos_y_cm:.1f}cm)"
                        angle_text = f"Angle: {transformed_angle_deg:.1f}°"
                        cv2.putText(warped, pos_text, (int(transformed_x) + 10, int(transformed_y)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        cv2.putText(warped, angle_text, (int(transformed_x) + 10, int(transformed_y) + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                # Print the internal markers information to console
                macData = self.get_macchinario("3d", frame)
                if macData is not None:
                    print(macData)
        else:
            # Use blank frame when no quadrilateral is found and no previous good corners
            # TODO: Mostrare comunque frame attuale per far capire che succede
            warped = frame

        # Show warped view only if display is enabled
        if display:
            cv2.imshow(self.warped_window_name, warped)

        # Return warped frame
        return warped

    def process_frame_data(self, frame=None) -> dict:
        """Process a frame and return marker data without displaying UI"""
        # If no frame is provided, use the current frame from the camera
        if frame is None:
            ret, frame = self.cam.read()
            if not ret:
                return {}

        # Find quadrilateral using ArUco markers - but don't display
        corners = self.find_quadrilateral(frame, display=False)

        # Convert to grayscale for ArUco detection (for all markers)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect all ArUco markers in the frame
        all_corners, all_ids, rejected = self.detector.detectMarkers(gray)

        # Update corners if found, otherwise use last good corners
        if corners is not None:
            # Update the last good corners when a valid quadrilateral is found
            self.last_good_corners = corners

        # If no valid corners available, return empty data
        if self.last_good_corners is None or all_ids is None:
            return {}

        # Get the perspective transform matrix
        src_pts = self.order_points(self.last_good_corners.astype(np.float32))
        dst_pts = np.array([
            [0, 0],
            [self.output_size[0] - 1, 0],
            [self.output_size[0] - 1, self.output_size[1] - 1],
            [0, self.output_size[1] - 1]
        ], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # Process markers
        result = {
            'markers': {},
            'robot': None
        }

        # Process all markers
        newData = False
        for i, marker_id in enumerate(all_ids.flatten()):
            # Skip corner markers
            if marker_id in self.marker_corners_ids:
                continue
            newData = True
            # Get marker corners
            marker_corners = all_corners[i][0]

            # Calculate center of the marker
            center_x = np.mean(marker_corners[:, 0])
            center_y = np.mean(marker_corners[:, 1])
            marker_center = np.array([center_x, center_y, 1.0])

            # Transform the center point to the warped coordinate system
            transformed_center = np.matmul(matrix, marker_center)
            transformed_x = transformed_center[0] / transformed_center[2]
            transformed_y = transformed_center[1] / transformed_center[2]

            # Convert pixel coordinates to cm from top-left
            pos_x_cm = transformed_x * self.scale_x
            pos_y_cm = transformed_y * self.scale_y

            # Calculate the orientation angle of the marker
            v1 = marker_corners[1] - marker_corners[0]  # Vector from top-right to bottom-right
            angle_rad = np.arctan2(v1[1], v1[0])

            # Transform two points along the direction vector to see how the angle transforms
            p1 = np.array([center_x, center_y, 1.0])
            p2 = np.array([center_x + np.cos(angle_rad) * 20, center_y + np.sin(angle_rad) * 20, 1.0])

            # Transform both points
            tp1 = np.matmul(matrix, p1)
            tp2 = np.matmul(matrix, p2)

            # Normalize the transformed points
            tp1 = tp1 / tp1[2]
            tp2 = tp2 / tp2[2]

            # Calculate the transformed angle
            transformed_angle_rad = np.arctan2(tp2[1] - tp1[1], tp2[0] - tp1[0])
            transformed_angle_deg = np.degrees(transformed_angle_rad)

            # Create marker data
            marker_data = {
                'id': int(marker_id),
                'position': [float(pos_x_cm), float(pos_y_cm)],
                'position_px': [float(transformed_x), float(transformed_y)],
                'angle': float(transformed_angle_deg)
            }

            # Check if this is the robot marker
            if marker_id == self.robot.get("aruco"):
                result['robot'] = marker_data
            else:
                result['markers'][self.macchinari_id.get(marker_id,f"unknown_{marker_id}")] = marker_data

        if newData and self.sendToRobot:
            # Send data to robot
            self.sendToRobot(result)

        return result

    def release(self):
        """Release camera and close all windows"""
        if self.cam is not None and self.cam.isOpened():
            self.cam.release()
        cv2.destroyAllWindows()

    def get_robot(self, frame=None):
        # If no frame is provided, use the current frame from the camera
        if frame is None:
            ret, frame = self.cam.read()
            if not ret:
                return None

        # Convert to grayscale for ArUco detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect all ArUco markers in the frame
        all_corners, all_ids, rejected = self.detector.detectMarkers(gray)

        # If no markers detected or no valid quadrilateral, return None
        if all_ids is None or self.last_good_corners is None:
            return None

        # Get the perspective transform matrix
        src_pts = self.order_points(self.last_good_corners.astype(np.float32))
        dst_pts = np.array([
            [0, 0],
            [self.output_size[0] - 1, 0],
            [self.output_size[0] - 1, self.output_size[1] - 1],
            [0, self.output_size[1] - 1]
        ], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # Look for the robot marker
        robot_data = None
        for i, marker_id in enumerate(all_ids.flatten()):
            if marker_id == self.robot:
                # This is the robot marker
                marker_corners = all_corners[i][0]

                # Calculate center of the marker
                center_x = np.mean(marker_corners[:, 0])
                center_y = np.mean(marker_corners[:, 1])
                marker_center = np.array([center_x, center_y, 1.0])

                # Transform the center point to the warped coordinate system
                transformed_center = np.matmul(matrix, marker_center)
                transformed_x = transformed_center[0] / transformed_center[2]
                transformed_y = transformed_center[1] / transformed_center[2]

                # Convert pixel coordinates to cm from top-left
                pos_x_cm = transformed_x * self.scale_x
                pos_y_cm = transformed_y * self.scale_y

                # Calculate the orientation angle of the marker
                v1 = marker_corners[1] - marker_corners[0]  # Vector from top-right to bottom-right
                angle_rad = np.arctan2(v1[1], v1[0])

                # Transform two points along the direction vector to see how the angle transforms
                p1 = np.array([center_x, center_y, 1.0])
                p2 = np.array([center_x + np.cos(angle_rad) * 20, center_y + np.sin(angle_rad) * 20, 1.0])

                # Transform both points
                tp1 = np.matmul(matrix, p1)
                tp2 = np.matmul(matrix, p2)

                # Normalize the transformed points
                tp1 = tp1 / tp1[2]
                tp2 = tp2 / tp2[2]

                # Calculate the transformed angle
                transformed_angle_rad = np.arctan2(tp2[1] - tp1[1], tp2[0] - tp1[0])
                transformed_angle_deg = np.degrees(transformed_angle_rad)

                # Create the robot data dictionary
                robot_data = {
                    "x": float(pos_x_cm),
                    "y": float(pos_y_cm),
                    "angle": float(transformed_angle_deg)
                }
                break

        return robot_data

    # Function to get the ArUco ID from the macchinario name
    def get_id_macchinario_from_name(self, key):
        return self.macchinari.get(key, {}).get("aruco", None)

    def get_macchinario(self, key="", frame=None):
        # If no frame is provided, use the current frame from the camera
        if frame is None:
            ret, frame = self.cam.read()
            if not ret:
                return None

        # Convert to grayscale for ArUco detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect all ArUco markers in the frame
        all_corners, all_ids, rejected = self.detector.detectMarkers(gray)

        # If no markers detected or no valid quadrilateral, return None
        if all_ids is None or self.last_good_corners is None:
            return None

        # Get the perspective transform matrix
        src_pts = self.order_points(self.last_good_corners.astype(np.float32))
        dst_pts = np.array([
            [0, 0],
            [self.output_size[0] - 1, 0],
            [self.output_size[0] - 1, self.output_size[1] - 1],
            [0, self.output_size[1] - 1]
        ], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # Look for the robot marker
        macchinario_data = None
        for i, marker_id in enumerate(all_ids.flatten()):
            if marker_id == self.get_id_macchinario_from_name(key=key):
                # This is the robot marker
                marker_corners = all_corners[i][0]

                # Calculate center of the marker
                center_x = np.mean(marker_corners[:, 0])
                center_y = np.mean(marker_corners[:, 1])
                marker_center = np.array([center_x, center_y, 1.0])

                # Transform the center point to the warped coordinate system
                transformed_center = np.matmul(matrix, marker_center)
                transformed_x = transformed_center[0] / transformed_center[2]
                transformed_y = transformed_center[1] / transformed_center[2]

                # Convert pixel coordinates to cm from top-left
                pos_x_cm = transformed_x * self.scale_x
                pos_y_cm = transformed_y * self.scale_y

                # Calculate the orientation angle of the marker
                v1 = marker_corners[1] - marker_corners[0]  # Vector from top-right to bottom-right
                angle_rad = np.arctan2(v1[1], v1[0])

                # Transform two points along the direction vector to see how the angle transforms
                p1 = np.array([center_x, center_y, 1.0])
                p2 = np.array([center_x + np.cos(angle_rad) * 20, center_y + np.sin(angle_rad) * 20, 1.0])

                # Transform both points
                tp1 = np.matmul(matrix, p1)
                tp2 = np.matmul(matrix, p2)

                # Normalize the transformed points
                tp1 = tp1 / tp1[2]
                tp2 = tp2 / tp2[2]

                # Calculate the transformed angle
                transformed_angle_rad = np.arctan2(tp2[1] - tp1[1], tp2[0] - tp1[0])
                transformed_angle_deg = np.degrees(transformed_angle_rad)

                # Create the robot data dictionary
                macchinario_data = {
                    "x": float(pos_x_cm),
                    "y": float(pos_y_cm),
                    "angle": float(transformed_angle_deg)
                }
                break

        return macchinario_data

    def run(self):
        # Override parent's run method to avoid showing the edge detection window
        while True:
            ret, frame = self.cam.read()
            if not ret:
                break

            self.process_frame(frame)
            ret = self.process_frame_data(frame)

            if ret:
                print(ret)

            # Press 'q' to exit
            if cv2.waitKey(1) == ord('q'):
                break

        self.cleanup()


# Example usage
if __name__ == '__main__':
    def send_to_robot(data):
        # Placeholder function to send data to the robot
        print("Sending data to robot:", data)


    with open('config.json') as f:
        d = json.load(f)
        corners_ids = [d['table']['aruco']['top-left'], d['table']['aruco']['top-right'], d['table']['aruco']['bottom-right'], d['table']['aruco']['bottom-left']]
        # TODO: Camera index dinamico con il nome della camera, vedi aruco-read

        transformer = ArUcoQuadrilateralTransformer(camera_index=d["cameraIndex"], marker_corners_ids=corners_ids,
                                                    robot=d['robot'], macchinari=d['macchinari'],
                                                    sendToRobot=send_to_robot)
        transformer.run()
