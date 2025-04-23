import cv2
import numpy as np
from typing import Callable, Optional, Tuple, List, Dict, Any

class ArUcoDetector:
    """Handles ArUco marker detection and related operations."""
    
    def __init__(self, aruco_dict_type: int = cv2.aruco.DICT_6X6_250):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
    
    def detect_markers(self, frame: np.ndarray) -> Tuple[List, Optional[np.ndarray], List]:
        """Detects ArUco markers in a frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("grayCam", gray)
        return self.detector.detectMarkers(gray)


class PerspectiveTransformer:
    """Handles perspective transformation operations."""

    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """Orders points in [top-left, top-right, bottom-right, bottom-left] order."""
        rect = np.zeros((4, 2), dtype=np.float32)

        # Top_Left                Top_right
        #   (0,0) --------------- (X_max,0)
        #     |                       |
        #     |                       |
        # (0,Y_max) ------------(X_max,Y_max)
        # Bottom_left             Bottom_right

        # La somma delle coordinate (x+y) è minima nell'angolo in alto a sinistra
        # e massima nell'angolo in basso a destra
        s = pts.sum(axis=1)
        tl_idx = np.argmin(s)  # Top-left
        br_idx = np.argmax(s)  # Bottom-right
        rect[0] = pts[tl_idx]
        rect[2] = pts[br_idx]

        # Trova i due punti rimanenti
        remaining_indices = [i for i in range(len(pts)) if i != tl_idx and i != br_idx]
        remaining_points = pts[remaining_indices]

        # Il punto top-right ha X maggiore e Y minore tra i due rimasti
        if remaining_points[0][0] > remaining_points[1][0] and remaining_points[0][1] < remaining_points[1][1]:
            rect[1] = remaining_points[0]  # Top-right
            rect[3] = remaining_points[1]  # Bottom-left
        elif remaining_points[1][0] > remaining_points[0][0] and remaining_points[1][1] < remaining_points[0][1]:
            rect[1] = remaining_points[1]  # Top-right
            rect[3] = remaining_points[0]  # Bottom-left
        else:
            # Se la condizione ideale non è soddisfatta, usa il punto con X maggiore come top-right
            tr_idx = np.argmax(remaining_points[:, 0])
            rect[1] = remaining_points[tr_idx]
            rect[3] = remaining_points[1 - tr_idx]
        return rect

    @staticmethod
    def transform_perspective(frame: np.ndarray, corners: np.ndarray, output_size: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """Applies perspective transform to the frame based on detected corners."""

        if corners is None:
            raise ValueError("Corners are None")
        if len(corners) != 4:
            raise ValueError(f"Corners are less than 4. ({len(corners)})")

        # Get ordered source points
        src_pts = PerspectiveTransformer.order_points(corners.astype(np.float32))

        def is_collinear(p1, p2, p3, epsilon=1e-5):
            # Calcola l'area del triangolo formato dai tre punti
            # Se l'area è (quasi) zero, i punti sono collineari
            area = abs((p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1]))
            return area < epsilon

        # Controlla che nessun gruppo di 3 punti sia collineare
        if (is_collinear(src_pts[0], src_pts[1], src_pts[2]) or
                is_collinear(src_pts[0], src_pts[1], src_pts[3]) or
                is_collinear(src_pts[0], src_pts[2], src_pts[3]) or
                is_collinear(src_pts[1], src_pts[2], src_pts[3])):
            raise ValueError("I punti di origine sono collineari e non possono definire una trasformazione prospettica")

        # Define destination points for the transform
        dst_pts = np.array([
            [0, 0],
            [output_size[0], 0],
            [output_size[0], output_size[1]],
            [0, output_size[1]]
        ], dtype=np.float32)

        # Verifica presenza di NaN o infiniti
        if np.any(np.isnan(src_pts)) or np.any(np.isnan(dst_pts)):
            raise ValueError("I punti contengono valori NaN")
        if np.any(np.isinf(src_pts)) or np.any(np.isinf(dst_pts)):
            raise ValueError("I punti contengono valori infiniti")

        # Calculate perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Apply perspective transform
        warped = cv2.warpPerspective(frame, matrix, output_size)
        
        return warped, matrix


class MarkerPoseCalculator:
    """Calculates poses of ArUco markers in the transformed space."""
    
    def __init__(self, width_cm: float, height_cm: float, output_size: Tuple[int, int]):
        self.width_cm = width_cm
        self.height_cm = height_cm
        self.output_size = output_size
        self.scale_x = self.width_cm / self.output_size[0]
        self.scale_y = self.height_cm / self.output_size[1]
    
    def calculate_marker_pose(self, marker_corners: np.ndarray, matrix: np.ndarray) -> Tuple[float, float, float, float, float]:
        """Calculates the transformed position (cm) and angle (radians) of a marker."""
        # Calculate center of the marker in original frame
        center_x = np.mean(marker_corners[:, 0])
        center_y = np.mean(marker_corners[:, 1])
        marker_center_orig = np.array([center_x, center_y, 1.0])
        
        # Transform the center point to the warped coordinate system
        transformed_center = np.matmul(matrix, marker_center_orig)
        transformed_x_px = transformed_center[0] / transformed_center[2]
        transformed_y_px = transformed_center[1] / transformed_center[2]
        
        # Convert pixel coordinates to cm from top-left of warped image
        pos_x_cm = transformed_x_px * self.scale_x
        pos_y_cm = transformed_y_px * self.scale_y
        
        # Calculate the orientation angle of the marker in the original frame
        v_orientation = marker_corners[1] - marker_corners[0]
        angle_rad_orig = np.arctan2(v_orientation[1], v_orientation[0])
        
        # To find the transformed angle, transform two points along the orientation vector
        p1_orig = np.array([center_x, center_y, 1.0])
        p2_orig = np.array([center_x + np.cos(angle_rad_orig) * 20,
                            center_y + np.sin(angle_rad_orig) * 20, 1.0])
        
        # Transform both points
        tp1 = np.matmul(matrix, p1_orig)
        tp2 = np.matmul(matrix, p2_orig)
        
        # Normalize the transformed points (perspective divide)
        tp1_norm = tp1 / tp1[2]
        tp2_norm = tp2 / tp2[2]
        
        # Calculate the angle of the vector between the transformed points
        transformed_angle_rad = np.arctan2(tp2_norm[1] - tp1_norm[1], tp2_norm[0] - tp1_norm[0])
        
        return pos_x_cm, pos_y_cm, transformed_angle_rad, transformed_x_px, transformed_y_px
    
    @staticmethod
    def apply_offset(x: float, y: float, angle_rad: float, config: Dict[str, Any]) -> Tuple[float, float, float]:
        """Applies configured offset to a pose."""
        offset_x = config.get("x_offset", 0.0)
        offset_y = config.get("y_offset", 0.0)
        offset_theta = config.get("theta_offset", 0.0)
        
        # Rotate offset vector by marker angle and add to position
        final_x = x + offset_x * np.cos(angle_rad) - offset_y * np.sin(angle_rad)
        final_y = y + offset_x * np.sin(angle_rad) + offset_y * np.cos(angle_rad)
        
        # Add angle offset and normalize to [-pi, pi]
        final_angle = angle_rad + offset_theta
        final_angle = (final_angle + np.pi) % (2 * np.pi) - np.pi
        
        return final_x, final_y, final_angle


class Visualizer:
    """Handles visualization of detected markers and transformed views."""
    
    @staticmethod
    def draw_quadrilateral(frame: np.ndarray, marker_centers: Dict[int, Tuple[float, float]]) -> np.ndarray:
        """Draws the quadrilateral connecting marker centers."""
        display_frame = frame.copy()
        
        if len(marker_centers) > 1:
            sorted_indices = sorted(marker_centers.keys())
            for i in range(len(sorted_indices)):
                pt1_idx = sorted_indices[i]
                pt2_idx = sorted_indices[(i + 1) % len(sorted_indices)]
                
                if pt1_idx in marker_centers and pt2_idx in marker_centers:
                    pt1 = tuple(map(int, marker_centers[pt1_idx]))
                    pt2 = tuple(map(int, marker_centers[pt2_idx]))
                    cv2.line(display_frame, pt1, pt2, (0, 255, 0), 2)
        
        return display_frame
    
    @staticmethod
    def draw_marker_info(warped: np.ndarray, marker_id: int, pos_x_cm: float, pos_y_cm: float, 
                         angle_rad: float, trans_x_px: float, trans_y_px: float, 
                         robot_config: Dict[str, Any], macchinari_id_to_key: Dict[int, str]) -> np.ndarray:
        """Draws marker information on the warped image."""
        angle_deg = np.degrees(angle_rad)
        
        # Draw center
        center_px = (int(trans_x_px), int(trans_y_px))
        cv2.circle(warped, center_px, 5, (0, 0, 255), -1)
        
        # Draw orientation line
        line_length = 30
        end_x = int(trans_x_px + line_length * np.cos(angle_rad))
        end_y = int(trans_y_px + line_length * np.sin(angle_rad))
        cv2.line(warped, center_px, (end_x, end_y), (0, 255, 0), 2)
        
        # Add text labels
        display_name = f"ID: {marker_id}"
        if marker_id == robot_config.get("aruco"):
            display_name = f"Robot ({marker_id})"
        elif marker_id in macchinari_id_to_key:
            display_name = f"{macchinari_id_to_key[marker_id]} ({marker_id})"
        
        pos_text = f"Pos: ({pos_x_cm:.1f}, {pos_y_cm:.1f})cm"
        angle_text = f"Ang: {angle_deg:.1f} deg"
        
        cv2.putText(warped, display_name, (center_px[0] + 10, center_px[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        cv2.putText(warped, pos_text, (center_px[0] + 10, center_px[1] + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        cv2.putText(warped, angle_text, (center_px[0] + 10, center_px[1] + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return warped


class Vision:
    """
    Detects a quadrilateral defined by four specific ArUco markers,
    performs perspective transformation on the camera feed based on these markers,
    and detects other ArUco markers within the transformed view, calculating their
    position and orientation in centimeters.
    """
    
    def __init__(self,
                 camera_index: int = 0,
                 aruco_dict_type: int = cv2.aruco.DICT_6X6_250,
                 marker_corners_ids: List[int] = [10, 12, 14, 16],
                 output_size: Tuple[int, int] = (800, 600),
                 width_cm: float = 30.0,
                 height_cm: float = 30.0,
                 robot: Dict[str, Any] = {"aruco": 18, "x_offset": 0, "y_offset": 0, "theta_offset": 0},
                 macchinari: Dict[str, Dict[str, Any]] = {
                     "3d": {"aruco": 20, "x_offset": 0, "y_offset": 0, "theta_offset": 0},
                     "laser": {"aruco": 21, "x_offset": 0, "y_offset": 0, "theta_offset": 0}
                 },
                 sendToRobot: Optional[Callable[[Dict[str, Any]], None]] = None,
                 display: bool = True):
        """Initializes the ArUcoQuadrilateralTransformer."""
        self.camera_index = camera_index
        self.output_size = output_size
        self.width_cm = width_cm
        self.height_cm = height_cm
        self.display = display
        self.marker_centers = {}
        
        # Initialize camera
        self.cam = cv2.VideoCapture(self.camera_index)
        if not self.cam.isOpened():
            raise IOError(f"Cannot open camera with index {self.camera_index}")
        
        self.frame_width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Initialize helper components
        self.aruco_detector = ArUcoDetector(aruco_dict_type)
        self.pose_calculator = MarkerPoseCalculator(width_cm, height_cm, output_size)
        
        # Expected marker IDs for the four corners
        if len(set(marker_corners_ids)) != 4:
            raise ValueError("marker_corners_ids must be 4 unique IDs.")
        self.marker_corners_ids = marker_corners_ids
        
        # Window names
        self.window_name = 'ArUco Detection View'
        self.warped_window_name = 'Transformed View'
        self.last_good_warped = None

        # Store configuration for robot and machines
        self.robot_config = robot
        self.macchinari_config = macchinari
        self.macchinari_id_to_key = {mData["aruco"]: key for key, mData in macchinari.items()}
        
        self.sendToRobot = sendToRobot
        self.last_good_corners = None
    
    def find_quadrilateral(self, frame: np.ndarray, display: bool = True) -> Optional[np.ndarray]:
        """Finds the quadrilateral defined by the specified ArUco corner markers."""
        corners, ids, rejected = self.aruco_detector.detect_markers(frame)
        
        if ids is None:
            if display:
                cv2.imshow(self.window_name, frame)
            raise ValueError("No ArUco markers detected.")

        # Map detected markers to their expected positions
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in self.marker_corners_ids:
                marker_corners_raw = corners[i][0]
                center_x = np.mean(marker_corners_raw[:, 0])
                center_y = np.mean(marker_corners_raw[:, 1])
                # Update marker_centers stored information with the new found center
                self.marker_centers[marker_id] = [center_x, center_y]
        
        # Draw detected markers if display is enabled
        if display:
            display_frame = frame.copy()
            cv2.aruco.drawDetectedMarkers(display_frame, corners, ids)
            if len(self.marker_centers) > 1:
                display_frame = Visualizer.draw_quadrilateral(display_frame, self.marker_centers)
            cv2.imshow(self.window_name, display_frame)
        
        # Return corners only if all four are found
        quad_corners = np.zeros((4, 2), dtype=np.float32)
        for index, cornerIds in enumerate(self.marker_corners_ids): # format return information as matrix vector
            quad_corners[index] = self.marker_centers.get(cornerIds, [0, 0])
        return quad_corners if len(self.marker_centers) == 4 else None

    def get_frame(self) -> np.ndarray:
        """Captures and returns a frame from the camera."""
        ret, frame = self.cam.read()
        if not ret:
            raise IOError("Error: Could not read frame from camera.")
        return frame
    
    def process_frame(self, frame: Optional[np.ndarray] = None, display: bool = True):
        """
        Processes a frame to find the quadrilateral and internal markers.
        Can optionally display visualization and return the processed frame.
        
        Args:
            frame: The input camera frame. If None, captures a new frame.
            display: Whether to display visualization windows.
            
        Returns:
            Nothing, to share information we use callback
        """
        # Capture frame if not provided
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame provided.")
        
        # Calculate the perspective transform matrix
        try:
            # Find quadrilateral corners
            corners = self.find_quadrilateral(frame, display=display)
            warped, matrix = PerspectiveTransformer.transform_perspective(frame, corners, self.output_size)
            # Save the last good warped frame
            self.last_good_warped = warped.copy()
        except Exception as e:
            print(f"Error calculating perspective transform: {type(e).__name__} - {e}")
            if display:
                if self.last_good_warped:
                    # Show the last good warped frame if available
                    cv2.imshow(self.warped_window_name, self.last_good_warped)
                else:
                    # Add error text to original frame
                    error_frame = frame.copy()
                    text = "No enough Corner available to generate field projection"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1.5  # Dimensione più grande
                    thickness = 3

                    # Calcola dimensioni del testo per centrarlo
                    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                    text_x = (error_frame.shape[1] - text_size[0]) // 2
                    text_y = (error_frame.shape[0] + text_size[1]) // 2

                    # Aggiunge contorno nero al testo per massimo contrasto
                    cv2.putText(error_frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2)
                    # Aggiunge testo in giallo per alta visibilità
                    cv2.putText(error_frame, text, (text_x, text_y), font, font_scale, (0, 255, 255), thickness)

                    cv2.imshow(self.warped_window_name, error_frame)
            return {}, frame if display else None
        
        all_corners, all_ids, rejected = self.aruco_detector.detect_markers(frame)
        if all_ids is None:
            raise ValueError("No markers detected.")

        # Prepare result structure
        result = {
            'markers': {},
            'robot': None
        }
        newData = False
        
        # Process all detected markers
        for i, marker_id_np in enumerate(all_ids.flatten()):
            marker_id = int(marker_id_np)
            
            # Skip corner markers
            if marker_id in self.marker_corners_ids:
                continue
            
            newData = True
            marker_corners = all_corners[i][0]
            
            # Calculate base pose
            try:
                pos_x_cm, pos_y_cm, angle_rad, trans_x_px, trans_y_px = self.pose_calculator.calculate_marker_pose(marker_corners, matrix)
            except Exception as e:
                print(f"Error calculating pose for marker {marker_id}: {e}")
                continue
            
            # Apply offsets based on marker type
            final_x_cm, final_y_cm, final_angle_rad = pos_x_cm, pos_y_cm, angle_rad
            is_robot = False

            if marker_id == self.robot_config.get("aruco"):
                final_x_cm, final_y_cm, final_angle_rad = MarkerPoseCalculator.apply_offset(pos_x_cm, pos_y_cm, angle_rad, self.robot_config)
                is_robot = True
            elif marker_id in self.macchinari_id_to_key:
                machine_config = self.macchinari_config.get(self.macchinari_id_to_key[marker_id], {})
                final_x_cm, final_y_cm, final_angle_rad = MarkerPoseCalculator.apply_offset(pos_x_cm, pos_y_cm, angle_rad, machine_config)
            
            # Store marker data
            marker_data = {
                'id': marker_id,
                'position': [float(final_x_cm), float(final_y_cm)],
                'angle': float(final_angle_rad),
                'position_px': [float(trans_x_px), float(trans_y_px)],
            }
            
            # Assign to the correct category in the result
            if is_robot:
                result['robot'] = marker_data
            else:
                marker_key = self.macchinari_id_to_key.get(marker_id, f"unknown_{marker_id}")
                result['markers'][marker_key] = marker_data
            
            # Draw marker information if display is enabled
            if display:
                warped = Visualizer.draw_marker_info(
                    warped, marker_id, pos_x_cm, pos_y_cm, angle_rad, trans_x_px, trans_y_px,
                    self.robot_config, self.macchinari_id_to_key)
        
        # Print final result of warped image with HUD information
        if display:
            cv2.imshow(self.warped_window_name, warped)
        
        # Send data if new data was processed and callback exists
        if newData and self.sendToRobot:
            try:
                self.sendToRobot(result) # send infornation using callback
            except Exception as e:
                print(f"Error calling sendToRobot callback: {e}")

        # Return the processed frame if display is enabled
        return
    
    def get_robot_pose(self, frame: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """Gets the current pose of the robot marker."""
        data = self.process_frame_data(frame)
        return data.get('robot', None)
    
    def get_macchinario_pose(self, key: str, frame: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """Gets the current pose of a specific machine marker by its key."""
        data = self.process_frame_data(frame)
        return data.get('markers', {}).get(key, None)
    
    def get_id_macchinario_from_name(self, key: str) -> Optional[int]:
        """Gets the ArUco ID associated with a machine name/key."""
        return self.macchinari_config.get(key, {}).get("aruco", None)
    
    def run(self):
        """Starts the main processing loop."""
        cv2.namedWindow(self.window_name)
        cv2.namedWindow(self.warped_window_name)
        
        while True:
            try:
                frame = self.get_frame()
                self.process_frame(frame, display=self.display)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Exit key 'q' pressed.")
                    break
        
            except (IOError, ValueError) as e:
                print(f"Error getting frame: {e}")
                continue
            
    
            
        self.cleanup()
    
    def cleanup(self):
        """Releases the camera and destroys all OpenCV windows."""
        print("Releasing camera and closing windows...")
        if self.cam is not None and self.cam.isOpened():
            self.cam.release()
        cv2.destroyAllWindows()
        print("Cleanup complete.")

