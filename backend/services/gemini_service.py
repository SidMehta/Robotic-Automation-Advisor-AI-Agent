import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

# Initialize Vertex AI
try:
    # GOOGLE_CLOUD_PROJECT is automatically set in App Engine runtime
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = "us-central1"  # Choose a region supporting the models
    vertexai.init(project=project_id, location=location)
    print(f"Vertex AI initialized for project: {project_id} in {location}")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    # Handle initialization error appropriately

# Configuration for generation
generation_config = GenerationConfig(
    temperature=0.4, # Adjust for creativity vs consistency
    max_output_tokens=8192,
)

# Function for video analysis using Gemini 1.5 Flash (supports video input)
def analyze_video_process(video_uri):
    """
    Analyzes the video at the given GCS URI to extract process steps.
    Args:
        video_uri: Google Cloud Storage URI (gs://bucket/video.mp4).
                   Direct YouTube links not directly supported by the API;
                   video needs to be accessible in GCS.
    Returns:
        A structured representation of the process steps or None if error.
    """
    print(f"Analyzing video from GCS URI: {video_uri}")
    try:
        # Ensure the URI starts with gs://
        if not video_uri or not video_uri.startswith("gs://"):
             raise ValueError("Invalid GCS URI provided for video analysis.")

        # Define the prompt for the model
        prompt = """Analyze the industrial process shown in this video.
        Break it down into a sequence of distinct tasks performed by humans or machines.
        Describe each task clearly, focusing on actions relevant for potential automation.
        Output the tasks as a JSON list, where each object has 'id' (sequential number), 'action' (description), and 'actor_type' ('human' or 'machine').
        Example: [{"id": 1, "action": "Pick up component X", "actor_type": "human"}, {"id": 2, "action": "Place component X in fixture", "actor_type": "human"}]
        """

        # Load the generative model (Gemini 1.5 Flash recommended for multimodal)
        # Make sure this model is available in your region 'us-central1'
        model = GenerativeModel("gemini-2.0-flash-001")

        # Prepare the video part
        video_part = Part.from_uri(video_uri, mime_type="video/mp4") # Adjust mime_type if needed

        # Generate content
        response = model.generate_content([video_part, prompt], generation_config=generation_config)

        print("Video analysis response received from Vertex AI.")
        # TODO: Add robust parsing and error handling for the response
        # Assuming the model follows the JSON instruction:
        import json
        try:
            # Extract JSON block if response includes ```json ... ```
            json_text_match = response.text.strip().split('```json')
            if len(json_text_match) > 1:
                json_text = json_text_match[1].split('```')[0].strip()
            else: # Assume raw JSON if no backticks
                json_text = response.text.strip()

            tasks = json.loads(json_text)
            print("Successfully parsed tasks from video analysis.")
            return tasks
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            print(f"Error parsing JSON response from video analysis: {e}")
            print(f"Raw response text: {response.text}")
            return None # Indicate failure

    except Exception as e:
        print(f"An error occurred during video analysis: {e}")
        return None

# Function for text-based analysis (options, cost-benefit)
def generate_text_analysis(prompt, model_name="gemini-2.5-pro-exp-03-25"):
    """
    Uses a text-based Gemini model via Vertex AI for analysis tasks.
    Args:
        prompt: The detailed prompt for the LLM.
        model_name: The name of the Gemini text model to use.
    Returns:
        The text response from the model, or None if error.
    """
    print(f"Generating text analysis with prompt (first 100 chars): {prompt[:100]}...")
    
    # For automation options, optimize token usage while preserving multiple options
    if "generate 1 to 3 distinct and plausible automation options" in prompt:
        # 1. Make reasons more concise
        prompt = prompt.replace(
            "1. For tasks ASSIGNED to a robot: Include a 'reason_automated' field explaining specifically WHY that robot is suitable (e.g., \"Payload (120kg est.) sufficient for lifting tire assembly (est. 30kg)\", \"Adequate reach (1.5m est.) for placement task\"). Reference estimated capabilities vs. inferred task needs. THIS FIELD IS MANDATORY for each assignment.",
            "1. For tasks ASSIGNED to a robot: Include a 'reason_automated' field (10-15 words max). THIS FIELD IS MANDATORY."
        )
        prompt = prompt.replace(
            "2. For human tasks NOT assigned: Include a 'reason_not_automated' field explaining the specific limiting factor (e.g., \"Requires fine dexterity beyond known robot capabilities\", \"Estimated reach (1.2m) insufficient for required range (est. 1.5m)\", \"Payload capacity (5kg) too low for estimated load (est. 7kg)\", \"Strategic choice: Kept manual to reduce tooling complexity in this option\"). Be specific about capability mismatches if applicable. THIS FIELD IS MANDATORY for each unassigned human task.",
            "2. For human tasks NOT assigned: Include a 'reason_not_automated' field (10-15 words max). THIS FIELD IS MANDATORY."
        )
        
        # 2. Eliminate markdown and explanatory text
        prompt = prompt.replace(
            "Your final output MUST be ONLY a single, valid JSON object conforming exactly to the specified format. Do not include any explanations, comments, code, or markdown formatting outside of the final JSON object itself. Adhere strictly to the required format below.",
            "Your final output MUST be ONLY the raw JSON with NO markdown formatting (no ```json, no ```), NO explanations, NO comments, and NO additional text whatsoever. ONLY emit the JSON itself."
        )
        
        # 3. Add stronger JSON formatting instructions
        prompt += """

EXTREMELY IMPORTANT:
- Output ONLY the raw JSON object with NO additional text or formatting
- Do NOT use markdown code blocks (no backticks/```)
- Do NOT add any explanations before or after the JSON
- Your output should start with { and end with }
- Ensure all arrays and objects have closing brackets
- Generate 2-3 distinctly different automation options (not more)
- Keep all reasoning very concise (10-15 words max per reason)
"""
        
        print("Added token optimization instructions while preserving multiple options")
    
    try:
        model = GenerativeModel(model_name)
        
        # Use lower temperature for more consistent output
        local_config = GenerationConfig(
            temperature=0.2,
            max_output_tokens=8192,
            top_p=0.95,
            top_k=40,
        )
        
        # Call generate_content
        response = model.generate_content(
            prompt, 
            generation_config=local_config
        )
        
        print("Text analysis response received from Vertex AI.")
        
        # Detailed diagnostics about the response
        if response.text:
            resp_text = response.text.strip()
            
            # Remove any markdown formatting if present despite instructions
            if resp_text.startswith("```") and resp_text.endswith("```"):
                resp_text = resp_text[3:-3].strip()
                if resp_text.startswith("json"):
                    resp_text = resp_text[4:].strip()
                print("WARNING: Removed markdown formatting from response")
                
            # Check if response begins with explanatory text
            if not resp_text.startswith("{"):
                first_brace = resp_text.find("{")
                if first_brace > 0:
                    resp_text = resp_text[first_brace:].strip()
                    print(f"WARNING: Removed {first_brace} characters of explanatory text from start of response")
            
            # Check if response has trailing text
            last_brace = resp_text.rfind("}")
            if last_brace < len(resp_text) - 1:
                resp_text = resp_text[:last_brace+1].strip()
                print(f"WARNING: Removed trailing text after the JSON")
            
            # Detailed diagnostics
            char_count = len(resp_text)
            line_count = resp_text.count('\n') + 1
            print(f"Response diagnostics:")
            print(f"- Character count: {char_count}")
            print(f"- Line count: {line_count}")
            print(f"- Last 50 chars: '{resp_text[-50:] if len(resp_text) > 50 else resp_text}'")
            
            # Check for truncation
            if not resp_text.endswith("}"):
                print("WARNING: Response may be truncated (does not end with '}')")
                
            # Check if we're near token limits
            if char_count > 7500:
                print(f"WARNING: Response is quite large ({char_count} chars), near token limits")
            
            # Count brackets to check for balance
            open_braces = resp_text.count('{')
            close_braces = resp_text.count('}')
            open_brackets = resp_text.count('[')
            close_brackets = resp_text.count(']')
            print(f"- Bracket balance: {open_braces}{{, {close_braces}}}, {open_brackets}[, {close_brackets}]")
            if open_braces != close_braces or open_brackets != close_brackets:
                print(f"WARNING: Unbalanced brackets detected (missing {open_braces - close_braces} '}}' and {open_brackets - close_brackets} ']')")
            
            # Return the cleaned response
            return resp_text
        else:
            return response.text
    except Exception as e:
        print(f"An error occurred during text generation: {e}")
        return None