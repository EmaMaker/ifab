from vision import Vision
import json

def send_to_robot_callback(data: Dict[str, Any]):
    """Placeholder callback function."""
    print("--- Sending Data ---")
    print(json.dumps(data, indent=2))
    print("--------------------")

# Configuration Loading
config_file_path = 'config.json'
try:
    with open(config_file_path, 'r') as f:
        config = json.load(f)
    
    camera_index = config.get("cameraIndex", 0)
    table_config = config.get("table", {})
    aruco_config = table_config.get("aruco", {})
    corners_ids = [
        aruco_config.get('top-left'),
        aruco_config.get('top-right'),
        aruco_config.get('bottom-right'),
        aruco_config.get('bottom-left')
    ]
    
    if None in corners_ids:
        raise ValueError("One or more corner ArUco IDs are missing in config.json table.aruco section.")
    
    output_width_px = table_config.get("output_width_px", 800)
    output_height_px = table_config.get("output_height_px", 600)
    physical_width_cm = table_config.get("physical_width_cm", 30.0)
    physical_height_cm = table_config.get("physical_height_cm", 30.0)
    
    robot_config = config.get("robot", {})
    macchinari_config = config.get("macchinari", {})
    
except FileNotFoundError:
    print(f"Error: Configuration file '{config_file_path}' not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{config_file_path}'. Check its format.")
    exit()
except KeyError as e:
    print(f"Error: Missing expected key in config.json: {e}")
    exit()
except ValueError as e:
    print(f"Error: Configuration value error: {e}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while loading configuration: {e}")
    exit()

# Initialize and Run Transformer
try:
    transformer = Vision(
        camera_index=camera_index,
        marker_corners_ids=corners_ids,
        output_size=(output_width_px, output_height_px),
        width_cm=physical_width_cm,
        height_cm=physical_height_cm,
        robot=robot_config,
        macchinari=macchinari_config,
        sendToRobot=send_to_robot_callback,
        display=True,
    )
    print("Initialization complete. Starting processing loop...")
    transformer.run()
    
except IOError as e:
    print(f"Camera Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred during execution: {e}")

print("Program finished.")