import cv2
import numpy as np
from canny_edge_detection import CannyEdgeDetector

class QuadrilateralTransformer(CannyEdgeDetector):
    def __init__(self, camera_index=0, lower_threshold=100, upper_threshold=200, 
                 blur_kernel=5, min_area=1000, output_size=(800, 600)):
        super().__init__(camera_index, lower_threshold, upper_threshold, blur_kernel)
        self.min_area = min_area
        self.output_size = output_size
        self.window_name = 'Quadrilateral Transformer'
        self.warped_window_name = 'Transformed View'
        self.last_good_corners = None  # Store the last valid quadrilateral

    def find_quadrilateral(self, edges):
        # Find contours in the edge image
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) < self.min_area:
            return None
        
        # Approximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # Check if the polygon has 4 vertices
        if len(approx) != 4:
            return None
        
        return approx.reshape(4, 2)

    def order_points(self, pts):
        # Order points in [top-left, top-right, bottom-right, bottom-left] order
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Top-left point will have the smallest sum
        # Bottom-right point will have the largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right point will have the smallest difference
        # Bottom-left point will have the largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    def transform_perspective(self, frame, corners):
        # Get ordered source points
        src_pts = self.order_points(corners.astype(np.float32))
        
        # Define destination points for the transform
        dst_pts = np.array([
            [0, 0],
            [self.output_size[0] - 1, 0],
            [self.output_size[0] - 1, self.output_size[1] - 1],
            [0, self.output_size[1] - 1]
        ], dtype=np.float32)
        
        # Calculate perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Apply perspective transform
        warped = cv2.warpPerspective(frame, matrix, self.output_size)
        
        return warped

    def process_frame(self, frame):
        # Get edge detection result from parent class
        gray_and_edges = super().process_frame(frame)
        edges = gray_and_edges[:, self.frame_width:]
        
        # Find quadrilateral in edges
        corners = self.find_quadrilateral(edges)
        
        # Create a blank frame with output size dimensions
        blank_frame = np.zeros((self.output_size[1], self.output_size[0], 3), dtype=np.uint8)
        
        if corners is not None:
            # Update the last good corners when a valid quadrilateral is found
            self.last_good_corners = corners
            # Transform the perspective when quadrilateral is found
            warped = self.transform_perspective(frame, corners)
        elif self.last_good_corners is not None:
            # Use the last good corners if available
            warped = self.transform_perspective(frame, self.last_good_corners)
        else:
            # Use blank frame when no quadrilateral is found and no previous good corners
            warped = blank_frame
        
        # Show warped view
        cv2.imshow(self.warped_window_name, warped)
        
        # Return warped frame (required by parent class but won't be displayed)
        return warped

    def run(self):
        # Override parent's run method to avoid showing the edge detection window
        while True:
            ret, frame = self.cam.read()
            if not ret:
                break
            
            self.process_frame(frame)
            
            # Press 'q' to exit
            if cv2.waitKey(1) == ord('q'):
                break
        
        self.cleanup()

# Example usage
if __name__ == '__main__':
    transformer = QuadrilateralTransformer(camera_index=0)
    transformer.run()
