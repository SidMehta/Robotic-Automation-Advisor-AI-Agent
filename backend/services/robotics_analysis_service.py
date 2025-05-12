import json
import math
import os # Make sure os is imported if using os.environ etc.

# Import other service modules using absolute path
import services.gemini_service as gemini_service
import services.urdf_service as urdf_service

# --- Helper Function for NEW Cost Calculation ---
def calculate_effective_robot_cost(robot_info, depreciation_years, hours_per_week, efficiency_gain):
    """
    Calculates the effective cost per human-equivalent minute for a single robot type.
    With added debugging to trace every step of the calculation.

    Args:
        robot_info (dict): Dictionary containing robot data like 'purchase_price' (C),
                           'op_cost_per_min' (O), 'end_effector_cost_percent' (E).
        depreciation_years (float): Depreciation life in years (T).
        hours_per_week (float): Operating hours per week (H).
        efficiency_gain (float): Efficiency gain vs human (G, e.g., 0.2 for 20% faster).

    Returns:
        float | str: The calculated effective cost per minute, or "N/A" if calculation fails.
    """
    robot_name = robot_info.get('robot_name', 'Unknown Robot')
    print(f"\n=== DETAILED COST CALCULATION FOR {robot_name} ===")
    print(f"Input parameters:")
    print(f"- Robot info: {robot_info}")
    print(f"- Depreciation years (T): {depreciation_years}")
    print(f"- Hours per week (H): {hours_per_week}")
    print(f"- Efficiency gain (G): {efficiency_gain}")
    
    try:
        C = robot_info.get('purchase_price')
        O = robot_info.get('op_cost_per_min')
        E = robot_info.get('end_effector_cost_percent')

        print(f"\nExtracted values:")
        print(f"- Purchase price (C): {C}")
        print(f"- Op cost per min (O): {O}")
        print(f"- End effector cost % (E): {E}")

        # --- Validate Inputs ---
        # Need Purchase Price (C) and OpEx (O) for basic calculation
        if O is None:
            print(f"WARNING: OpEx (O) is missing for robot {robot_name}. Cannot calculate effective cost.")
            return "N/A" # Cannot proceed without OpEx

        # If Capex (C) or End Effector % (E) is missing, we can't calculate Capex_per_min
        # However, if C is 0 or null, Capex_per_min is effectively 0. Let's proceed if O is known.
        C_float = 0.0
        if C is not None:
           try:
               C_float = float(C)
               print(f"Converted purchase price: C_float = {C_float}")
           except (ValueError, TypeError):
               print(f"WARNING: Invalid purchase price (C) for {robot_name}. Treating Capex as 0 for cost calc.")
               # Continue calculation, but Capex component will be 0
        else:
            print(f"WARNING: Purchase price (C) is None for {robot_name}. Treating Capex as 0.")

        # Assume E is 0 if missing/null
        E_float = 0.0
        if E is not None:
            try:
                E_float = float(E)
                print(f"Converted end effector %: E_float = {E_float}")
            except (ValueError, TypeError):
                print(f"WARNING: Invalid end effector cost % (E) for {robot_name}. Assuming 0%.")
        else:
            print(f"WARNING: End effector % (E) is None for {robot_name}. Assuming 0%.")

        # Ensure T, H, G, O are valid numbers (should be checked before calling, but double check)
        T = float(depreciation_years)
        H = float(hours_per_week)
        G = float(efficiency_gain)
        O_float = float(O)

        print(f"\nValidated input values:")
        print(f"- C_float = {C_float}")
        print(f"- E_float = {E_float}")
        print(f"- T = {T}")
        print(f"- H = {H}")
        print(f"- G = {G}")
        print(f"- O_float = {O_float}")

        if T <= 0 or H <= 0:
            print("WARNING: Depreciation years (T) and Hours per week (H) must be positive.")
            return "N/A"
        if (1 + G) <= 0:
            # Avoid division by zero or negative efficiency denominator
            # If robot is 100% slower or more (G <= -1), effective cost is infinite or undefined
            print(f"WARNING: Efficiency gain (G) implies non-positive work rate ({1+G=}). Cannot calculate effective cost.")
            return "N/A"

        # --- Perform Calculations ---
        print("\nCalculation steps:")
        
        # Step 1: Calculate total CAPEX
        total_capex = C_float * (1.0 + E_float)
        print(f"1. Total CAPEX = C × (1 + E) = {C_float} × (1 + {E_float}) = {total_capex}")
        
        # Step 2: Calculate total operating minutes in life
        total_operating_minutes_in_life = T * 52.0 * H * 60.0
        print(f"2. Total operating minutes in life = T × 52 × H × 60 = {T} × 52 × {H} × 60 = {total_operating_minutes_in_life}")
        
        # Step 3: Calculate CAPEX per minute
        capex_per_min = 0.0
        if total_operating_minutes_in_life > 0: # Avoid division by zero
             capex_per_min = total_capex / total_operating_minutes_in_life
        print(f"3. CAPEX per minute = Total CAPEX / Total minutes = {total_capex} / {total_operating_minutes_in_life} = {capex_per_min}")
        
        # Step 4: Calculate raw cost per minute (CAPEX + OPEX)
        robot_raw_cost_per_min = capex_per_min + O_float
        print(f"4. Raw cost per minute = CAPEX/min + OPEX/min = {capex_per_min} + {O_float} = {robot_raw_cost_per_min}")
        
        # Step 5: Adjust for efficiency
        robot_effective_cost_per_human_min = robot_raw_cost_per_min / (1.0 + G)
        print(f"5. Effective cost per human-equivalent minute = Raw cost / (1 + G) = {robot_raw_cost_per_min} / (1 + {G}) = {robot_effective_cost_per_human_min}")
        
        print(f"\nFINAL EFFECTIVE COST: ${robot_effective_cost_per_human_min:.6f} per human-equivalent minute")
        return robot_effective_cost_per_human_min

    except (ValueError, TypeError, ZeroDivisionError) as e:
        print(f"ERROR calculating effective cost for {robot_name}: {e}")
        return "N/A"


# --- Updated Recommendation Logic with Robust CAPEX Calculation ---
def determine_recommendation_new(cost_benefit_results, human_cost_min, automation_options, tasks, depreciation_years, hours_per_week, available_robots=None):
    """
    Determines recommendation based on effective robot cost vs human cost,
    accounting for the number of tasks automated and projecting annual savings.
    
    Args:
        cost_benefit_results: List of cost comparison data for each option
        human_cost_min: Human cost per minute
        automation_options: List of automation options with assignments
        tasks: List of all process tasks
        depreciation_years: Number of years for depreciation (for projection)
        hours_per_week: Operating hours per week
        available_robots: List of available robots with metadata
    
    Returns:
        Recommendation dictionary with option ID and justification
    """
    best_option_id = None
    highest_total_savings = -float('inf')
    best_option_details = {}
    
    # Task and cycle assumptions
    task_duration_mins = 1.0  # Assume each task takes 1 minute
    weeks_per_year = 52
    
    # Calculate accurate cycles per hour based on total task count
    human_tasks = [t for t in tasks if t.get('actor_type') == 'human']
    total_human_tasks = len(human_tasks)
    cycle_time_mins = total_human_tasks * task_duration_mins  # Full cycle takes this many minutes
    cycles_per_hour = 60 / cycle_time_mins if cycle_time_mins > 0 else 1  # How many cycles fit in an hour
    cycles_per_year = cycles_per_hour * hours_per_week * weeks_per_year
    
    print(f"Process metrics: {total_human_tasks} human tasks, {cycle_time_mins} mins per cycle, {cycles_per_hour:.2f} cycles/hour, {cycles_per_year:.2f} cycles/year")
    
    # Check for valid data
    if not cost_benefit_results or human_cost_min <= 0:
        return {
            "recommended_option_id": None,
            "justification": "No valid cost comparison data available or human cost is non-positive."
        }
    
    option_savings = []
    annual_projections = []
    
    # Create a lookup table for robot metadata
    robot_metadata = {}
    if available_robots:
        for robot in available_robots:
            robot_name = robot.get('robot_name')
            if robot_name:
                robot_metadata[robot_name] = robot
    
    for i, option_result in enumerate(cost_benefit_results):
        option_id = option_result['option_id']
        robot_costs = option_result.get('robot_cost_comparison', [])
        
        # Get corresponding automation option details
        automation_option = None
        for opt in automation_options:
            if opt.get('option_id') == option_id:
                automation_option = opt
                break
        
        if not automation_option:
            print(f"Warning: Couldn't find automation option with ID {option_id}")
            continue
            
        # Count automated tasks and build robot assignment map
        assignments = automation_option.get('assignments', [])
        num_automated_tasks = len(assignments)
        task_to_robot_map = {assign['task_id']: assign['robot_name'] for assign in assignments}
        
        # Create a lookup for robot costs
        robot_cost_map = {}
        for robot_comp in robot_costs:
            robot_name = robot_comp.get('robot_name')
            cost = robot_comp.get('robot_effective_cost_per_human_min')
            if isinstance(cost, (int, float)):
                robot_cost_map[robot_name] = cost
        
        # Calculate costs for this option for one complete cycle
        total_cost_with_automation_per_cycle = 0
        total_human_cost_per_cycle = 0
        
        # Calculate cost if ALL human tasks were done manually
        for task in human_tasks:
            task_id = task.get('id')
            human_cost = human_cost_min * task_duration_mins
            total_human_cost_per_cycle += human_cost
            
            # Now calculate the actual cost with automation
            if task_id in task_to_robot_map:
                # This task is automated
                robot_name = task_to_robot_map[task_id]
                if robot_name in robot_cost_map:
                    robot_cost = robot_cost_map[robot_name] * task_duration_mins
                    total_cost_with_automation_per_cycle += robot_cost
                else:
                    # If we don't have robot cost data, use human cost as fallback
                    total_cost_with_automation_per_cycle += human_cost
            else:
                # This task remains manual
                total_cost_with_automation_per_cycle += human_cost
        
        # Calculate savings per cycle
        savings_per_cycle = total_human_cost_per_cycle - total_cost_with_automation_per_cycle
        
        # Calculate annual costs and savings
        annual_human_cost = total_human_cost_per_cycle * cycles_per_year
        annual_cost_with_automation = total_cost_with_automation_per_cycle * cycles_per_year
        annual_savings = savings_per_cycle * cycles_per_year
        
        # Get robot purchase prices and calculate CAPEX properly
        unique_robots = set(task_to_robot_map.values())
        robot_capex = 0
        missing_capex_data = False
        
        # Calculate total CAPEX for all robots used in this option
        for robot_name in unique_robots:
            # Try to find the robot in the metadata
            robot_purchase_price = None
            robot_end_effector_pct = 0.25  # Default
            
            # First check the robot_metadata from available_robots
            if robot_name in robot_metadata:
                robot_info = robot_metadata[robot_name]
                if 'purchase_price' in robot_info:
                    robot_purchase_price = robot_info['purchase_price']
                if 'end_effector_cost_percent' in robot_info:
                    robot_end_effector_pct = robot_info['end_effector_cost_percent']
            
            # Handle null or missing purchase price
            if robot_purchase_price is None or not isinstance(robot_purchase_price, (int, float)):
                print(f"Warning: Robot '{robot_name}' has no valid purchase price. Using default estimate.")
                # Use a default estimate based on similar robots
                if 'atlas' in robot_name.lower():
                    robot_purchase_price = 250000  # Similar to atlas models
                elif 'jvrc' in robot_name.lower():
                    robot_purchase_price = 150000  # Match known jvrc price
                elif 'digit' in robot_name.lower():
                    robot_purchase_price = 200000  # Match known digit price
                elif 'ggc' in robot_name.lower() or 'testmodel' in robot_name.lower():
                    robot_purchase_price = 180000  # Estimate for GGC_TestModel
                else:
                    robot_purchase_price = 100000  # Conservative default
                
                missing_capex_data = True
            
            # Calculate and add to total CAPEX
            robot_total_cost = robot_purchase_price * (1 + robot_end_effector_pct)
            robot_capex += robot_total_cost
            
            print(f"Robot CAPEX calculation: {robot_name} - Purchase: ${robot_purchase_price:.2f}, End effector: {robot_end_effector_pct*100:.1f}%, Total: ${robot_total_cost:.2f}")
        
        if missing_capex_data:
            print(f"Warning for {option_id}: Some robots had missing purchase price data. Estimates were used.")
        
        print(f"Total CAPEX for {option_id}: ${robot_capex:.2f}")
        
        # Store projection data for the chart
        # Store projection data for the chart
        option_projection = {
            "option_id": option_id,
            "baseline_cost_per_cycle": total_human_cost_per_cycle,
            "robot_cost_per_cycle": total_cost_with_automation_per_cycle,
            "annual_baseline_cost": annual_human_cost,
            "annual_cost_with_automation": annual_cost_with_automation,
            "robot_capex": robot_capex,
            "cumulative_costs_by_year": [
                # Year 0 is just capex
                robot_capex,
            ],
            "baseline_cumulative_costs_by_year": [
                0,  # Year 0 has no cost
            ]
        }

        # Debug the chart data for this option
        print(f"\n=== CHART DATA FOR {option_id} ===")
        print(f"Initial CAPEX: ${robot_capex:.2f}")
        print(f"Annual cost with automation: ${annual_cost_with_automation:.2f}")
        print(f"Annual baseline cost: ${annual_human_cost:.2f}")
        print(f"Cumulative costs by year: {option_projection['cumulative_costs_by_year']}")
        print(f"Baseline cumulative costs by year: {option_projection['baseline_cumulative_costs_by_year']}")
        
        
        # Verify all chart data is valid
        # Verify all chart data is valid
        for i, cost in enumerate(option_projection['cumulative_costs_by_year']):
            if not isinstance(cost, (int, float)) or math.isnan(cost) or math.isinf(cost):
                print(f"WARNING: Invalid chart data for year {i}: {cost}")
                # Fix invalid data
                option_projection['cumulative_costs_by_year'][i] = robot_capex if i == 0 else (robot_capex + annual_cost_with_automation * i)
                
        for i, cost in enumerate(option_projection['baseline_cumulative_costs_by_year']):
            if not isinstance(cost, (int, float)) or math.isnan(cost) or math.isinf(cost):
                print(f"WARNING: Invalid baseline chart data for year {i}: {cost}")
                # Fix invalid data
                option_projection['baseline_cumulative_costs_by_year'][i] = 0 if i == 0 else (annual_human_cost * i)



        
        # Calculate cumulative costs for years 1-N
        # Calculate cumulative costs for years 1-N
        for year in range(1, int(depreciation_years) + 1):
            # Automation option: CAPEX + (OPEX × years)
            cumulative_cost = robot_capex + (annual_cost_with_automation * year)
            option_projection["cumulative_costs_by_year"].append(cumulative_cost)
            
            # Baseline: OPEX × years
            baseline_cumulative = annual_human_cost * year
            option_projection["baseline_cumulative_costs_by_year"].append(baseline_cumulative)
            
            # Debug output - show if automation is more expensive at each year
            print(f"Year {year}: {option_id} = ${cumulative_cost:,.2f}, No Automation = ${baseline_cumulative:,.2f}")
            diff = cumulative_cost - baseline_cumulative
            if diff > 0:
                print(f"  → {option_id} costs ${diff:,.2f} MORE than No Automation in Year {year}")
            else:
                print(f"  → {option_id} costs ${-diff:,.2f} LESS than No Automation in Year {year}")

        
        annual_projections.append(option_projection)
        
        # Count tasks that use robots cheaper than humans
        num_tasks_with_savings = 0
        for task_id, robot_name in task_to_robot_map.items():
            if robot_name in robot_cost_map:
                if robot_cost_map[robot_name] < human_cost_min:
                    num_tasks_with_savings += 1
        
        # Store option details for comparison
        option_savings.append({
            "option_id": option_id,
            "num_automated_tasks": num_automated_tasks,
            "num_tasks_with_savings": num_tasks_with_savings,
            "savings_per_cycle": savings_per_cycle,
            "annual_savings": annual_savings,
            "percent_savings": (savings_per_cycle / total_human_cost_per_cycle * 100) if total_human_cost_per_cycle > 0 else 0
        })
        
        # Check if this is the best option so far based on annual savings
        # Check if this is the best option so far based on annual savings
        # Only consider options that actually SAVE money (positive savings)
        if annual_savings > highest_total_savings and annual_savings > 0:
            highest_total_savings = annual_savings
            best_option_id = option_id
            best_option_details = {
                "num_automated_tasks": num_automated_tasks,
                "num_tasks_with_savings": num_tasks_with_savings,
                "savings_per_cycle": savings_per_cycle,
                "annual_savings": annual_savings,
                "percent_savings": (savings_per_cycle / total_human_cost_per_cycle * 100) if total_human_cost_per_cycle > 0 else 0
            }
    
    # Prepare recommendation
    # Prepare recommendation
    if best_option_id and highest_total_savings > 0:
        # Format percentage with 1 decimal place
        percent_savings = round(best_option_details.get("percent_savings", 0), 1)
        annual_savings = best_option_details.get("annual_savings", 0)
        savings_per_cycle = best_option_details.get("savings_per_cycle", 0)
        
        justification = (
            f"Option {best_option_id} recommended. "
            f"It automates {best_option_details.get('num_automated_tasks', 0)} tasks, "
            f"saving ${savings_per_cycle:.2f} per process cycle "
            f"(${annual_savings:.2f} annually, {percent_savings}% reduction). "
            f"{best_option_details.get('num_tasks_with_savings', 0)} of these tasks use robots that are cheaper than human labor."
        )
    else:
        # No cost-effective option found - recommend keeping manual process
        best_option_id = "No_Automation"
        justification = (
            "No automation option is cost-effective. All analyzed options would increase costs compared to manual labor. "
            "Recommendation: Keep process manual unless non-financial factors (quality, consistency, safety) justify automation."
        )

    # ALWAYS return a valid recommendation object
    return {
        "recommended_option_id": best_option_id,
        "justification": justification,
        "option_savings": option_savings,
        "annual_projections": annual_projections,
        "chart_data_verified": True  # Add flag to confirm data has been verified
    }



# --- Main Orchestration Function ---
# Modified to accept new inputs and use new calculation logic
def perform_full_analysis(video_uri, human_cost_min, # Existing
                          depreciation_years, hours_per_week, efficiency_gain # New financial inputs
                         ):
    """
    Orchestrates the full robotic advisor analysis workflow using new cost logic.
    """
    print("Starting full robotics analysis (using Effective Cost per Min logic)...")

    # --- Validate Numeric Inputs ---
    try:
        t_float = float(depreciation_years)
        h_float = float(hours_per_week)
        g_float = float(efficiency_gain) / 100.0  # Convert from percentage to decimal
        print(f"Converting efficiency gain from {efficiency_gain}% to {g_float} decimal")
        oh_float = float(human_cost_min)
        # Default robot cost isn't directly used in new calc, but keep OH check
        if oh_float <= 0:
             raise ValueError("Human cost per minute must be positive.")
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid financial input provided: {e}")
        return {"error": f"Invalid financial input provided: {e}"}

    # --- Step 1: Analyze Video (using LLM) ---
    tasks = gemini_service.analyze_video_process(video_uri)
    if not tasks or not isinstance(tasks, list):
        print("Analysis failed: Could not analyze video or invalid task format.")
        tasks = [] # Ensure tasks is a list
        # Consider returning error if tasks are essential
        return {"error": "Failed to analyze video process or received invalid task format."}
    print(f"Step 1 complete: Identified {len(tasks)} tasks.")


    # --- Step 2: Get Robot Info & Generate Automation Options (using LLM) ---
    available_robots = urdf_service.get_available_robots() # Includes metadata now
    if not available_robots:
        print("Analysis warning: No available robot definitions found or parsed.")
        # Cannot proceed without robot data for new calculation logic
        return {"error": "No available robot definitions found (required for cost analysis)."}

    # Use the latest prompt asking for detailed reasoning (from previous step)
    prompt_step2 = f"""
    You are an extremely meticulous robotics automation engineer evaluating potential solutions.
    Your task is to analyze the process tasks and available robots provided below, and then generate 1 to 3 distinct and plausible automation options, focusing on replacing 'human' tasks.
    For each option, you MUST provide detailed justifications IN THE JSON OUTPUT:
    1. For tasks ASSIGNED to a robot: Include a 'reason_automated' field explaining specifically WHY that robot is suitable (e.g., "Payload (120kg est.) sufficient for lifting tire assembly (est. 30kg)", "Adequate reach (1.5m est.) for placement task"). Reference estimated capabilities vs. inferred task needs. THIS FIELD IS MANDATORY for each assignment.
    2. For human tasks NOT assigned: Include a 'reason_not_automated' field explaining the specific limiting factor (e.g., "Requires fine dexterity beyond known robot capabilities", "Estimated reach (1.2m) insufficient for required range (est. 1.5m)", "Payload capacity (5kg) too low for estimated load (est. 7kg)", "Strategic choice: Kept manual to reduce tooling complexity in this option"). Be specific about capability mismatches if applicable. THIS FIELD IS MANDATORY for each unassigned human task.
    Your final output MUST be ONLY a single, valid JSON object conforming exactly to the specified format. Do not include any explanations, comments, code, or markdown formatting outside of the final JSON object itself. Adhere strictly to the required format below.

    Input Data Context:
    - 'Process Tasks': A list detailing steps from a video, including 'id', 'action' description, and 'actor_type'.
    {json.dumps(tasks, indent=2)}

    - 'Available Robots': A list of robots, including 'robot_name' and *estimated* capabilities ('estimated_reach_m', 'estimated_payload_kg'). These capabilities are estimates.
    {json.dumps(available_robots, indent=2)}

    Analysis Requirements & Guidelines:
    1. Identify 'human' tasks.
    2. For each option (1-3 distinct options):
        a. Decide assignments based on inferred task requirements vs. estimated robot capabilities.
        b. Populate 'assignments' list including 'task_id', 'robot_name', and the mandatory, specific 'reason_automated' string.
        c. Populate 'unassigned_human_tasks' list including 'task_id' and the mandatory, specific 'reason_not_automated' string.
    3. Aim for diverse options.
    4. Provide a brief overall 'summary'.
    5. Do not assign 'machine' tasks.

    Required Output Format:
    Output ONLY the following JSON structure. Ensure valid JSON syntax (double quotes for all keys and string values). No extra text or formatting.

    {{
      "automation_options": [
        {{
          "option_id": "String",
          "summary": "String",
          "assignments": [
            {{
              "task_id": Number,
              "robot_name": "String",
              "reason_automated": "String" // MANDATORY: Specific reason robot IS suitable (link capability to task).
            }}
          ],
          "unassigned_human_tasks": [
            {{
              "task_id": Number,
              "reason_not_automated": "String" // MANDATORY: Specific reason task NOT automated (limitation/strategy).
            }}
          ]
        }}
      ]
    }}
    """ # End of prompt_step2 f-string

    options_text = gemini_service.generate_text_analysis(prompt_step2)
    automation_options = [] # Default to empty list
    
    if options_text:
        try:
            # Extract JSON block if response includes ```json ... ``` or similar
            json_text = options_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
            elif json_text.startswith("```"): # Handle potential ``` without json specifier
                 json_text = json_text[3:]
                 if json_text.endswith("```"):
                    json_text = json_text[:-3]

            # First try to parse the JSON as-is
            try:
                automation_options_data = json.loads(json_text.strip())
                print("Successfully parsed complete JSON response")
            except json.JSONDecodeError as json_err:
                print(f"Initial JSON parsing error: {json_err}")
                print("Attempting to extract complete options from truncated JSON...")
                
                # Check if we can find the automation_options structure
                if '"automation_options": [' in json_text:
                    # Try to extract any complete options even if the JSON is truncated
                    automation_options = []
                    
                    # Find the start of the options array
                    options_start = json_text.find('"automation_options": [') + len('"automation_options": [')
                    
                    # Look for complete option objects
                    option_start = json_text.find('{', options_start)
                    
                    while option_start != -1:
                        # Find a potential end of this option object by counting braces
                        brace_count = 1
                        potential_end = option_start + 1
                        
                        while brace_count > 0 and potential_end < len(json_text):
                            if json_text[potential_end] == '{':
                                brace_count += 1
                            elif json_text[potential_end] == '}':
                                brace_count -= 1
                            potential_end += 1
                        
                        # If we found a complete option, try to parse it
                        if brace_count == 0:
                            option_json = json_text[option_start:potential_end]
                            try:
                                option_obj = json.loads(option_json)
                                automation_options.append(option_obj)
                                print(f"Successfully extracted option {option_obj.get('option_id', 'unknown')}")
                            except json.JSONDecodeError:
                                # If this option doesn't parse, it might have nested quotes issue
                                print(f"Could not parse option at position {option_start}")
                            
                            # Look for the next option
                            option_start = json_text.find('{', potential_end)
                        else:
                            # We hit the end without finding a complete option
                            break
                    
                    if automation_options:
                        print(f"Extracted {len(automation_options)} complete option(s) from truncated JSON")
                        automation_options_data = {"automation_options": automation_options}
                    else:
                        # If no options could be extracted, make an empty structure
                        print("Could not extract any complete options from truncated JSON")
                        automation_options_data = {"automation_options": []}
                else:
                    # If we don't find the basic structure, use an empty default
                    print("Could not find automation_options array in response")
                    automation_options_data = {"automation_options": []}
            
            automation_options = automation_options_data.get("automation_options", [])
            if not isinstance(automation_options, list):
                print("Warning: 'automation_options' from LLM Step 2 was not a list. Defaulting to empty.")
                automation_options = []
            
            print(f"Step 2 complete: Parsed {len(automation_options)} automation options.")
        except Exception as e:
             print(f"Error processing response from options generation (Step 2): {e}")
             print(f"Raw response text:\n{options_text}")
             automation_options = [] # Proceed with empty options

    else:
        print("Analysis warning: Could not generate automation options (Step 2 received no text).")


    # --- Step 3: Calculate Effective Costs & Compare (using Python) ---
    print("Step 3: Calculating effective robot costs in Python...")
    cost_benefit_results_new = []
    robot_data_map = {r['robot_name']: r for r in available_robots} # For easy lookup

    if automation_options:
        for option in automation_options:
            option_id = option.get('option_id', 'Unknown Option')
            assignments = option.get('assignments', [])
            unique_robots_in_option = set(assign['robot_name'] for assign in assignments)

            robot_cost_comparison = []
            for robot_name in unique_robots_in_option:
                robot_info = robot_data_map.get(robot_name)
                if robot_info:
                    effective_cost = calculate_effective_robot_cost(
                        robot_info,
                        t_float,  # Depreciation years
                        h_float,  # Hours per week
                        g_float   # Efficiency gain
                    )
                    robot_cost_comparison.append({
                        "robot_name": robot_name,
                        "robot_effective_cost_per_human_min": effective_cost,
                        "human_cost_per_min": oh_float,
                        "is_cheaper": "N/A" if not isinstance(effective_cost, (int, float)) else (effective_cost < oh_float)
                    })
                else:
                     print(f"Warning: Robot '{robot_name}' in option '{option_id}' not found in available_robots list.")
                     # Optionally add an entry indicating data was missing
                     robot_cost_comparison.append({
                         "robot_name": robot_name,
                         "robot_effective_cost_per_human_min": "N/A",
                         "human_cost_per_min": oh_float,
                         "is_cheaper": "N/A"
                     })


            cost_benefit_results_new.append({
                "option_id": option_id,
                "robot_cost_comparison": robot_cost_comparison
                # Add back summary if needed: "summary": option.get('summary')
            })
        print(f"Cost comparison calculations complete for {len(cost_benefit_results_new)} options.")
    else:
         print("Skipping cost comparison calculation as no automation options were generated or parsed.")

    # Determine recommendation based on the cost comparison results 
    # with accurate cycle calculation and annual projections
    # Determine recommendation based on the cost comparison results 
    # with accurate cycle calculation and annual projections
    recommendation = determine_recommendation_new(
        cost_benefit_results_new,
        oh_float,
        automation_options, 
        tasks,              # Pass the tasks list
        t_float,            # Pass depreciation_years
        h_float,            # Pass hours_per_week
        available_robots    # Pass available robots for metadata access
    )
    print("Step 3 complete: Recommendation determined with task count and robust CAPEX calculations.")

    # --- Step 4: Combine results ---
    # Ensure recommendation is never None
    if recommendation is None:
        recommendation = {
            "recommended_option_id": "No_Automation",
            "justification": "No recommendation available due to missing cost data or calculation error.",
            "option_savings": [],
            "annual_projections": []
        }
        print("WARNING: Generated fallback recommendation due to None value")
    
    final_results = {
        "process_tasks": tasks,
        "available_robots": available_robots,
        "automation_options": automation_options,
        "cost_benefit_analysis": cost_benefit_results_new,
        "recommendation": recommendation,
        "task_savings_analysis": recommendation.get("option_savings", []),
        "annual_projections": recommendation.get("annual_projections", [])
    }
    print("Full robotics analysis completed successfully (with robust CAPEX calculations).")
    return final_results