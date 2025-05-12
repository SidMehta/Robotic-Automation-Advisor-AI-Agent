import React, { useState } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip'; // For helper text on efficiency
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'; // Optional icon

function RoboticsInputForm({ onSubmit, isLoading }) {
    // --- State for existing and NEW inputs ---
    const [videoUri, setVideoUri] = useState('');
    const [humanCostMin, setHumanCostMin] = useState('');
    const [depreciationYears, setDepreciationYears] = useState(''); // NEW (T)
    const [hoursPerWeek, setHoursPerWeek] = useState('');       // NEW (H)
    const [efficiencyGain, setEfficiencyGain] = useState('');     // NEW (G)
    // --- Removed: amortizationYears, robotCostMin ---

    const [uriError, setUriError] = useState(false);

    const validateUri = (uri) => {
        if (uri && !uri.startsWith("gs://")) {
            setUriError(true);
            return false;
        }
        setUriError(false);
        return true;
    };

    const handleUriChange = (event) => {
        setVideoUri(event.target.value);
        validateUri(event.target.value);
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        // Updated validation
        if (!validateUri(videoUri) || !humanCostMin || !depreciationYears || !hoursPerWeek || efficiencyGain === '') { // Check efficiencyGain is not empty string
             console.error("Validation failed on submit");
            // Optionally show a more user-friendly error message
            alert('Please fill in all fields correctly.');
            return;
        }

        // --- Pass NEW data structure to onSubmit ---
        onSubmit({
            video_uri: videoUri,
            human_cost_min: parseFloat(humanCostMin),
            depreciation_years: parseFloat(depreciationYears),
            hours_per_week: parseFloat(hoursPerWeek),
            efficiency_gain: parseFloat(efficiencyGain),
        });
    };

    // Updated validation check for button disabling
    const isFormInvalid = !videoUri || uriError || !humanCostMin || !depreciationYears || !hoursPerWeek || efficiencyGain === '';

    return (
        <Paper elevation={3} sx={{ padding: 3, marginBottom: 3, maxWidth: '600px', margin: '20px auto' }}>
            <Box component="form" onSubmit={handleSubmit} noValidate autoComplete="off">
                <Typography variant="h5" component="h2" gutterBottom>
                    Robotic Process Analysis Input
                </Typography>
                <Stack spacing={2.5}> {/* Increased spacing slightly */}
                    <TextField
                        label="Video GCS URI"
                        variant="outlined"
                        fullWidth
                        required
                        id="videoUri"
                        value={videoUri}
                        onChange={handleUriChange}
                        placeholder="gs://your-bucket-name/your-video.mp4"
                        error={uriError}
                        helperText={uriError ? "URI must start with gs://" : "Google Cloud Storage path to video"}
                    />
                    <TextField
                        label="Average Human Cost per Minute ($)"
                        variant="outlined"
                        fullWidth
                        required
                        type="number"
                        id="humanCostMin"
                        value={humanCostMin}
                        onChange={(e) => setHumanCostMin(e.target.value)}
                        placeholder="e.g., 0.75"
                        inputProps={{ min: 0.01, step: 0.01 }} // Min > 0 usually makes sense
                    />
                    {/* --- New Input Fields --- */}
                    <TextField
                        label="Depreciation Life (Years)"
                        variant="outlined"
                        fullWidth
                        required
                        type="number"
                        id="depreciationYears" // T
                        value={depreciationYears}
                        onChange={(e) => setDepreciationYears(e.target.value)}
                        placeholder="e.g., 7"
                        inputProps={{ min: 1, step: 1 }}
                    />
                    <TextField
                        label="Operating Hours per Week"
                        variant="outlined"
                        fullWidth
                        required
                        type="number"
                        id="hoursPerWeek" // H
                        value={hoursPerWeek}
                        onChange={(e) => setHoursPerWeek(e.target.value)}
                        placeholder="e.g., 40 or 80 for 2 shifts"
                        inputProps={{ min: 1, max: 168, step: 1 }} // Max 168 hours/week
                    />
                     <TextField
                        label="Est. Robot Efficiency Gain (%) vs Human"
                        variant="outlined"
                        fullWidth
                        required
                        type="number"
                        id="efficiencyGainPercent" // Input as percentage for user-friendliness
                        value={efficiencyGain} // Store as percentage string
                        onChange={(e) => setEfficiencyGain(e.target.value)}
                        placeholder="e.g., 20 for 20% faster, 0 for same, -10 for 10% slower"
                        InputProps={{ // Add helper icon/tooltip
                          endAdornment: (
                            <Tooltip title="Enter percentage gain. E.g., 20 means robot is 20% faster (takes 1/(1+0.2) = 0.83 mins per human-minute of work). 0 means same speed. -10 means 10% slower.">
                              <InfoOutlinedIcon color="action" sx={{ cursor: 'help' }} />
                            </Tooltip>
                          ),
                        }}
                        helperText="Enter as percentage (e.g., 20, 0, -10)"
                    />
                     {/* --- Removed: Amortization Period, Default Robot Op Cost --- */}

                    <Box sx={{ position: 'relative' }}>
                        <Button
                            type="submit"
                            variant="contained"
                            color="primary"
                            disabled={isLoading || isFormInvalid}
                            fullWidth
                            size="large"
                            sx={{ mt: 1 }}
                        >
                            {isLoading ? 'Analyzing...' : 'Analyze Process'}
                        </Button>
                        {isLoading && (
                            <CircularProgress
                                size={24}
                                sx={{
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    marginTop: '-12px',
                                    marginLeft: '-12px',
                                }}
                            />
                        )}
                    </Box>
                </Stack>
            </Box>
        </Paper>
    );
}

export default RoboticsInputForm;