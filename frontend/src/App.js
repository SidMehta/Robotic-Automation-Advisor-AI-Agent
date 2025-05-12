import React, { useState, useCallback } from 'react';
import axios from 'axios'; // Ensure axios is imported
// Import your CSS
import './App.css';
// Import Components
import RoboticsInputForm from './components/RoboticsInputForm';
import RoboticsResultsDisplay from './components/RoboticsResultsDisplay';
// Import MUI components for layout
import Container from '@mui/material/Container';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
// Box is not explicitly used in this App.js version but can be kept for future use if needed

function App() {
    // State for loading indicator and results/error
    const [isLoading, setIsLoading] = useState(false);
    const [analysisResults, setAnalysisResults] = useState(null);
    // NEW STATE: To store the inputs used for the current analysis, needed for the chart
    const [currentUserInputs, setCurrentUserInputs] = useState(null);

    // Define the base URL for the backend API
    const API_BASE_URL = '/api'; // Assumes proxy or relative deployment

    // Callback function passed to the form, triggered on submit
    const handleAnalysisSubmit = useCallback(async (formData) => {
        // Store the inputs that led to this analysis request
        setCurrentUserInputs(formData); // <-- ADDED THIS LINE

        setIsLoading(true);
        setAnalysisResults(null); // Clear previous results before new request
        console.log("Sending data to backend (New Logic):", formData);

        try {
            const response = await axios.post(`${API_BASE_URL}/analyze_robotics`, formData);
            console.log("Received response from backend:", response.data);
            setAnalysisResults(response.data);
        } catch (err) {
            console.error("API call failed:", err);
            let errorMessage = "Failed to analyze process.";
            if (err.response && err.response.data && err.response.data.error) {
                errorMessage = `Error: ${err.response.data.error}`;
            } else if (err.message) {
                errorMessage = err.message;
            }
            // Update analysisResults state to show error in the display component
            setAnalysisResults({ error: errorMessage });
        } finally {
            setIsLoading(false);
        }
    }, []); // Empty dependency array is okay

    return (
        <div className="App">
            <AppBar position="static" sx={{ marginBottom: 2 }}>
                <Toolbar>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Robotic Process Advisor
                    </Typography>
                </Toolbar>
            </AppBar>

            <Container maxWidth="lg">
                 <main>
                     <RoboticsInputForm onSubmit={handleAnalysisSubmit} isLoading={isLoading} />

                     {/*
                       Render the results display if analysisResults is not null.
                       Pass the full results object, the available_robots list,
                       AND the currentUserInputs (which holds T, H, G, OH for the chart).
                     */}
                     {analysisResults &&
                         <RoboticsResultsDisplay
                             results={analysisResults}
                             availableRobots={analysisResults.available_robots}
                             userInput={currentUserInputs} // <-- ADDED THIS PROP
                         />
                     }
                 </main>
            </Container>
        </div>
    );
}

export default App;