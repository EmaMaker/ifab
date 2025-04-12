import cv2
import numpy as np

class CannyEdgeDetector:
    def __init__(self, camera_index=0, lower_threshold=100, upper_threshold=200, blur_kernel=5, window_name='Canny Edge Detection'):
        self.camera_index = camera_index
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.blur_kernel = blur_kernel
        self.window_name = window_name
        # Initialize camera
        self.cam = cv2.VideoCapture(camera_index)
        
        # Get frame dimensions
        self.frame_width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Window name
        self.window_name = 'Canny Edge Detection'
        
    def setup_window(self):
        # Create window and trackbars
        cv2.namedWindow(self.window_name)
                
        # Create trackbars for edge detection parameters
        cv2.createTrackbar('Lower Threshold', self.window_name, self.lower_threshold, 255, lambda x: None)
        cv2.createTrackbar('Upper Threshold', self.window_name, self.upper_threshold, 255, lambda x: None)
        cv2.createTrackbar('Blur Kernel', self.window_name, self.blur_kernel, 15, lambda x: None)
    
    def update_parameters(self):
        # Get current trackbar values
        self.lower_threshold = cv2.getTrackbarPos('Lower Threshold', self.window_name)
        self.upper_threshold = cv2.getTrackbarPos('Upper Threshold', self.window_name)
        self.blur_kernel = cv2.getTrackbarPos('Blur Kernel', self.window_name)
        
        # Ensure blur kernel is odd
        self.blur_kernel = self.blur_kernel if self.blur_kernel % 2 == 1 else self.blur_kernel + 1
    
    def process_frame(self, frame):
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)
        
        # Apply Canny edge detection
        edges = cv2.Canny(blurred, self.lower_threshold, self.upper_threshold)
        
        # Stack images horizontally for comparison
        return np.hstack((gray, edges))
    
    def run(self):
        self.setup_window()
        
        while True:
            ret, frame = self.cam.read()
            if not ret:
                break
            
            self.update_parameters()
            display = self.process_frame(frame)
            
            # Display the result
            cv2.imshow(self.window_name, display)
            
            # Press 'q' to exit
            if cv2.waitKey(1) == ord('q'):
                break
        
        self.cleanup()
    
    def cleanup(self):
        self.cam.release()
        cv2.destroyAllWindows()

# Example usage
if __name__ == '__main__':
    detector = CannyEdgeDetector(camera_index=0)
    detector.run()