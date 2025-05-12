import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Define path to assets relative to this file's directory (adjust if needed)
# App Engine deployment structure needs careful path handling
# Assuming assets folder is at backend/assets
ASSETS_DIR = Path(__file__).parent.parent / 'assets'
URDF_DIR = ASSETS_DIR / 'urdfs'
METADATA_FILE = ASSETS_DIR / 'robot_metadata.json'

def load_robot_metadata():
    """Loads robot metadata (costs) from the JSON file."""
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
            print(f"Loaded metadata for {len(metadata)} robots from {METADATA_FILE}")
            return metadata
    except FileNotFoundError:
        print(f"Warning: Metadata file not found at {METADATA_FILE}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {METADATA_FILE}")
        return {}

def parse_urdf_capabilities(urdf_file_path):
    """
    Parses a URDF file to extract a basic capability summary.
    Placeholder - very basic parsing. Real capability analysis is complex.
    """
    try:
        tree = ET.parse(urdf_file_path)
        root = tree.getroot()
        robot_name = root.get('name', 'Unknown Robot')
        num_links = len(root.findall('link'))
        num_joints = len(root.findall('joint'))

        # Basic heuristic (needs significant improvement for real analysis)
        reach_approx = num_links * 0.5 # Extremely rough guess
        payload_approx = num_links * 2  # Extremely rough guess

        capabilities = {
            "robot_name": robot_name,
            "num_links": num_links,
            "num_joints": num_joints,
            "estimated_reach_m": reach_approx, # Placeholder value
            "estimated_payload_kg": payload_approx # Placeholder value
        }
        # print(f"Parsed basic capabilities for {robot_name} from {urdf_file_path}")
        return capabilities

    except ET.ParseError:
        print(f"Warning: Error parsing XML from {urdf_file_path}")
        return None
    except FileNotFoundError:
         print(f"Warning: URDF file not found at {urdf_file_path}")
         return None


def get_available_robots():
    """
    Lists available robots by scanning the URDF directory,
    parsing capabilities, and merging with metadata.
    """
    print(f"Scanning for URDF files in: {URDF_DIR}")
    available_robots = []
    metadata = load_robot_metadata()

    if not URDF_DIR.is_dir():
         print(f"Warning: URDF directory not found at {URDF_DIR}")
         return []

    for urdf_file in URDF_DIR.glob('*.urdf'):
        print(f"Processing URDF file: {urdf_file.name}")
        capabilities = parse_urdf_capabilities(urdf_file)
        if capabilities:
            # Merge capabilities with metadata
            robot_info = capabilities
            meta = metadata.get(urdf_file.name, {}) # Get metadata using filename as key
            robot_info['purchase_price'] = meta.get('purchase_price', None) # e.g., 50000
            robot_info['op_cost_per_min'] = meta.get('op_cost_per_min', None) # e.g., 0.5
            robot_info['urdf_filename'] = urdf_file.name
            available_robots.append(robot_info)

    print(f"Found {len(available_robots)} robots with parsed info.")
    return available_robots