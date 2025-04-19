from flask import Flask, request, jsonify
from aruco_quadrilateral_transformer import ArUcoQuadrilateralTransformer
import threading
import time
import json

app = Flask(__name__)

# Class to manage the transformer in a separate thread
class TransformerThread:
    def __init__(self, camera_index=0):
        self.transformer = None
        self.thread = None
        self.running = False
        self.camera_index = camera_index
        self.lock = threading.Lock()
        self.marker_data = {}
    
    def start(self, **kwargs):
        if self.running:
            return False
        
        # Create transformer with provided parameters
        self.transformer = ArUcoQuadrilateralTransformer(camera_index=self.camera_index, **kwargs)
        
        # Start thread
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        if not self.running:
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        
        # Release camera resources
        if self.transformer:
            self.transformer.release()
            self.transformer = None
        
        return True
    
    def _run(self):
        if not self.transformer:
            return
        
        while self.running:
            # Process frame and get marker data
            frame_data = self.transformer.process_frame_data()
            
            # Update marker data with thread safety
            if frame_data:
                with self.lock:
                    self.marker_data = frame_data
            
            # Small delay to prevent CPU overuse
            time.sleep(0.01)
    
    def get_robot(self):
        if not self.transformer:
            return None

        return self.transformer.get_robot()

# Create transformer thread instance
transformer_thread = TransformerThread()

@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the IFAB Vision API'})


@app.route('/api/transformer/start', methods=['POST'])
def start_transformer():
    print("start")    
    # Get parameters from request or use defaults
    # Load configuration from JSON file
    try:
        with open('vision/config.json') as f:
            config = json.load(f)
            camera_index = 0
            marker_ids = [
                config['table']['aruco']['top-left'],
                config['table']['aruco']['top-right'],
                config['table']['aruco']['bottom-right'],
                config['table']['aruco']['bottom-left']
            ]
            min_area = 1000
            output_size = [800, 600]
            width_cm = config['table']['width']
            height_cm = config['table']['height']
            robot = config['robot']
            macchinari = config['macchinari']
    except FileNotFoundError:
        return jsonify({'error': 'Configuration file not found'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid configuration file format'}), 500
    
    # Update camera index if provided
    transformer_thread.camera_index = camera_index
    
    # Start the transformer thread
    success = transformer_thread.start(
        marker_ids=marker_ids,
        min_area=min_area,
        output_size=output_size,
        width_cm=width_cm,
        height_cm=height_cm,
        robot=robot,
        macchinari=macchinari
    )
    
    if success:
        return jsonify({'status': 'started'})
    else:
        return jsonify({'error': 'Transformer already running'}), 400

@app.route('/api/transformer/stop', methods=['POST'])
def stop_transformer():
    success = transformer_thread.stop()
    
    if success:
        return jsonify({'status': 'stopped'})
    else:
        return jsonify({'error': 'Transformer not running'}), 400

@app.route('/api/transformer/status', methods=['GET'])
def transformer_status():
    is_running = transformer_thread.running
    marker_data = transformer_thread.get_marker_data() if is_running else {}
    
    return jsonify({
        'running': is_running,
        'marker_data': marker_data
    })

@app.route('/api/transformer/robot', methods=['GET'])
def get_robot_data():
    if not transformer_thread.running:
        return jsonify({'error': 'Transformer not running'}), 400
    
    robot_data = transformer_thread.get_robot()
    
    return jsonify({
        'robot': robot_data
    })



if __name__ == '__main__':
    app.run(debug=True)