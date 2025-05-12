import os
import traceback # For logging errors
from flask import Blueprint, request, jsonify

# Import only the service needed for robotics analysis
# Make sure the service filename matches what you have (e.g., robotics_analysis_service.py)
try:
    import services.robotics_analysis_service as robotics_analysis_service
    print("Successfully imported robotics_analysis_service")
except ImportError as e:
     print(f"ERROR importing robotics_analysis_service: {e}")
     # Define a placeholder if import fails, so route registration doesn't crash
     class PlaceholderService:
         def perform_full_analysis(*args, **kwargs):
             return {"error": "Robotics analysis service failed to load."}
     robotics_analysis_service = PlaceholderService()


# Define the Blueprint
main_bp = Blueprint('main', __name__)

# === Robotics Advisor Route (Updated for New Cost Logic) ===

@main_bp.route('/api/analyze_robotics', methods=['POST'])
def analyze_robotics():
    """
    Endpoint to trigger the robotic advisor analysis using new cost logic.
    Expects JSON payload with:
    - video_uri (string, gs://...)
    - human_cost_min (float)
    - depreciation_years (float, T)
    - hours_per_week (float, H)
    - efficiency_gain (float, G - e.g., 0.2 for 20%)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # --- Get existing and NEW inputs ---
        video_uri = data.get('video_uri')
        human_cost_min = data.get('human_cost_min')
        depreciation_years = data.get('depreciation_years') # NEW (T)
        hours_per_week = data.get('hours_per_week')       # NEW (H)
        efficiency_gain = data.get('efficiency_gain')     # NEW (G)
        # --- Remove old inputs: amortization_years, robot_cost_min ---

        # --- Updated Validation ---
        required_fields = ['video_uri', 'human_cost_min', 'depreciation_years', 'hours_per_week', 'efficiency_gain']
        missing = [field for field in required_fields if field not in data or data[field] is None]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        if not isinstance(video_uri, str) or not video_uri.startswith("gs://"):
             return jsonify({"error": "Invalid video_uri: Must be a string starting with gs://..."}), 400

        # Convert numeric types safely
        try:
            oh_float = float(human_cost_min)
            t_float = float(depreciation_years)
            h_float = float(hours_per_week)
            g_float = float(efficiency_gain)
            # Perform basic range checks if desired (e.g., T > 0, H > 0)
            if t_float <= 0 or h_float <= 0:
                 raise ValueError("Depreciation years and hours per week must be positive.")
            # Note: efficiency_gain (G) can be negative, zero or positive
            if oh_float <= 0:
                 raise ValueError("Human cost per minute must be positive.")

        except (ValueError, TypeError) as e:
             return jsonify({"error": f"Invalid numerical input: {e}"}), 400


        # --- Trigger the analysis with NEW arguments ---
        print(f"Received robotics analysis request (New Logic) for video: {video_uri}")
        results = robotics_analysis_service.perform_full_analysis(
            video_uri=video_uri,
            human_cost_min=oh_float,          # Pass validated human cost
            depreciation_years=t_float,       # Pass validated T
            hours_per_week=h_float,           # Pass validated H
            efficiency_gain=g_float           # Pass validated G
        )
        # ---------------------------------------------

        # --- Handle Response ---
        if isinstance(results, dict) and results.get("error"):
             print(f"Analysis service reported error: {results['error']}")
             return jsonify(results), 500 # Keep 500 for server-side processing errors
        else:
            print("Analysis successful, returning results (New Logic).")
            return jsonify(results), 200

    except Exception as e:
        print(f"CRITICAL Error in /api/analyze_robotics endpoint: {e}")
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"error": "An unexpected server error occurred."}), 500