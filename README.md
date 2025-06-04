# 🤖 Robotic Process Advisor AI Agent [MIT Lab Project]

An agentic‑AI web app that watches an industrial‑process video, plans robot‑automation options with LLMs, and delivers a data‑driven cost‑benefit recommendation.

## 🖼 Screenshots

| User Input | Task Breakdown |
|----------------|-----------------|
| <img width="600" alt="input_highincome_country" src="https://github.com/user-attachments/assets/cd67ef40-2d72-42fe-9354-5f302e0aab30" /> | <img width="600" alt="task_flow" src="https://github.com/user-attachments/assets/32b52aac-ddc3-41bd-8603-3b44442c296e" />|

| Automation Options | Cost Projections Table |
|----------------|-----------------|
| <img width="600" alt="automation_options" src="https://github.com/user-attachments/assets/803bdd5a-949b-41cb-8261-f64d34aed5c8" />|<img width="600" alt="costbenefit" src="https://github.com/user-attachments/assets/e5b27e8d-bfe6-4738-8476-0f5f7b469354" />|

| Cost Projections Chart |
|-----------------|
| <img width="600" alt="chartandreco_highincome" src="https://github.com/user-attachments/assets/904d3dbd-58dd-428a-b192-87d9fcfb0f50" />|

---

## ✨ Agentic Flow Highlights

| 🍱 Ingredient | Role in the Flow |
|--------------|------------------|
| **Gemini Multimodal (Vertex AI)** | *Perception agent* – turns the uploaded video into a structured task list (`actor_type = human/machine`). |
| **Gemini Text (Vertex AI)** | *Planning agent* – maps human tasks to available robot URDFs and explains automation decisions. |
| **Python Orchestrator** (`robotics_analysis_service.py`) | *Control loop* – chains LLM calls, injects URDF data, sanitises JSON, then hands off to deterministic cost logic. |
| **Knowledge Base (URDF + metadata)** | RAG grounding for the prompts. |
| **Deterministic Cost Engine** | Calculates effective robot cost / min, projects cash flows & ROI. |
| **React Front‑end** | Shows a React‑Flow task diagram and a Chart.js cost projection, making the AI’s reasoning auditable. |

---

## 📜 System Architecture


<img src="https://github.com/user-attachments/assets/a861b1d3-97fc-4a0d-96b0-64d380af196b" alt="System architecture" width="750"/>

---

## 🏗 Project Structure

~~~text
robotic-advisor/
│
├── frontend/                       # React frontend application
│   ├── app.yaml                    # Google App Engine configuration for frontend
│   ├── package.json                # NPM dependencies and scripts
│   ├── public/                     # Static public assets
│   └── src/                        # React source code
│       ├── App.js                  # Main React component
│       ├── App.css                 # Main application styles
│       ├── index.js                # React entry point
│       ├── index.css               # Global styles
│       └── components/             # React components
│           ├── RoboticsInputForm.js    # Form for user inputs
│           ├── RoboticsResultsDisplay.js  # Display for analysis results
│           ├── ProcessDiagram.js      # Visualizes task breakdown using React Flow
│           ├── TimeSeriesFinancialChart.js  # Cost projections visualization
│           └── CostBenefitChart.js    # Cost-benefit analysis charts
│
├── backend/                        # Python/Flask backend application
|   ├── assets/                         # Shared assets and resources
|      ├── urdfs/                      # Robot URDF definition files
|      │   ├── atlas_convex_hull.urdf  # Example robot URDF
|      │   ├── atlas_v4_with_multisense.urdf
|      │   ├── digit_model.urdf
|      │   ├── GGC_TestModel_rx78_20170112.urdf
|      │   ├── jvrc1.urdf
|      │   └── x1.urdf
|      └── robot_metadata.json         # Robot financial and operational metadata
│   ├── app.yaml                    # Google App Engine configuration for backend
│   ├── requirements.txt            # Python dependencies
│   ├── app.py                      # Flask application setup
│   ├── .env                        # Environment variables (for local development)
│   └── app/                        # Application package
│       ├── __init__.py             # Package initialization
│       ├── main.py                 # API endpoints and routes
│       └── services/               # Service modules
│           ├── __init__.py         # Package initialization
│           ├── gemini_service.py   # Vertex AI Gemini API integration
│           ├── urdf_service.py     # URDF file parsing and robot data
│           └── robotics_analysis_service.py  # Core analysis orchestration
~~~

---

## 💰 Cost Model (formula)

~~~text
EffectiveRobotCost =
  [ (Purchase Price × (1 + End‑Effector %)) / (T years × 52 × H hrs × 60)
    + OpEx $/min ]
  ÷ (1 + Efficiency Gain decimal)
~~~

The engine annualises that figure, projects cumulative cost to the depreciation horizon, and picks the option with the lowest total spend.



---

## 🙋‍♀️ Questions

* Feel free to ping me on [LinkedIn](https://linkedin.com/in/sidmehta91).

> _“LLMs are most useful when they **decide**, but don’t **guess** – the deterministic Python in between keeps them honest.”_
