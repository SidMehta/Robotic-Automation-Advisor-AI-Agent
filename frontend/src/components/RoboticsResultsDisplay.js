import React from 'react'; // Import React for useMemo
import ProcessDiagram from './ProcessDiagram';
import TimeSeriesFinancialChart from './TimeSeriesFinancialChart'; // Import the new chart component

// MUI Imports (ensure all needed components are imported)
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Divider from '@mui/material/Divider';

// Define common styles for consistency
const sectionPaperStyle = {
    padding: { xs: 1.5, sm: 2, md: 3 }, // Responsive padding
    marginBottom: 3,
    margin: 'auto',
    maxWidth: '950px' // Slightly wider max width
};

const headingStyle = {
    marginBottom: 2,
    borderBottom: '1px solid',
    borderColor: 'divider',
    paddingBottom: 1,
    fontWeight: 'medium', // Make headings slightly bolder
};

// Expect 'results', 'availableRobots', AND 'userInput' as props
function RoboticsResultsDisplay({ results, availableRobots, userInput }) {

    // Hooks called unconditionally at the top level
    const robotCapabilitiesMap = React.useMemo(() =>
        new Map((availableRobots || []).map(r => [r.robot_name, { reach: r.estimated_reach_m, payload: r.estimated_payload_kg }]))
    , [availableRobots]);

    const taskActorMap = React.useMemo(() =>
        new Map((results?.process_tasks || []).map(t => [t.id, t.actor_type]))
    , [results?.process_tasks]);


    // --- 1. Handle No Results or Error ---
    if (!results) {
        return null; // Render nothing if results are not yet available
    }
    if (results.error) {
        // Display error message using MUI Paper for consistent styling
        return (
            <Paper elevation={3} sx={{ ...sectionPaperStyle, color: 'error.main', border: '1px solid', borderColor: 'error.main' }}>
                <Typography variant="h6" component="h3" gutterBottom>Error:</Typography>
                <Typography>{results.error}</Typography>
            </Paper>
        );
    }

    // --- 2. Destructure Results (Safely provide defaults) ---
    const {
        process_tasks = [],
        automation_options = [],
        cost_benefit_analysis = [], // Expected new structure
        recommendation = {}
    } = results;

    // --- 3. Render Component ---
    return (
        // Use Box for overall padding/margin if needed
        <Box sx={{ padding: { xs: 1, sm: 2 }, marginTop: 2 }}>
            <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ marginBottom: 3 }}>
                Analysis Results
            </Typography>

            {/* Section 1: Process Breakdown */}
            <Paper elevation={2} sx={{ ...sectionPaperStyle }}>
                <Typography variant="h5" component="h3" sx={{ ...headingStyle }}>Process Breakdown</Typography>
                {/* Ensure ProcessDiagram handles empty tasks gracefully */}
                <ProcessDiagram tasks={process_tasks} />
                 <Typography variant="h6" component="h4" sx={{ marginTop: 2, marginBottom: 1 }}>Original Task List:</Typography>
                 <List dense disablePadding>
                    {(process_tasks.length > 0) ? process_tasks.map(task => (
                        <ListItem key={`orig-task-${task.id}`} divider sx={{ py: 0.5 }}>
                            <ListItemText
                                primary={`Task ${task.id}: ${task.action}`}
                                secondary={`Original Actor: ${task.actor_type}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                                secondaryTypographyProps={{ variant: 'caption' }}
                            />
                        </ListItem>
                    )) : <Typography variant="body2" sx={{ fontStyle: 'italic', ml: 2 }}>No tasks identified.</Typography>}
                </List>
            </Paper>

            {/* Section 2: Automation Options */}
            <Paper elevation={2} sx={{ ...sectionPaperStyle }}>
                <Typography variant="h5" component="h3" sx={{ ...headingStyle }}>Automation Options</Typography>
                {automation_options.length === 0 ? <Typography sx={{ fontStyle: 'italic', ml: 1 }}>No automation options generated.</Typography> : (
                    automation_options.map((option, index) => {
                        // Define maps inside this loop, as they depend on the specific option
                        const assignmentsMap = new Map((option.assignments || []).map(a => [a.task_id, { robot: a.robot_name, reason: a.reason_automated }]));
                        const unassignedTasks = option.unassigned_human_tasks || [];
                        const unassignedReasonsMap = new Map(unassignedTasks.map(u => [u.task_id, u.reason_not_automated]));

                        return (
                            <Card key={option.option_id || `option-${index}`} sx={{ marginBottom: 3, padding: 2 }} variant="outlined">
                                <Typography variant="h6" component="h4" gutterBottom sx={{ fontWeight: 'medium' }}>
                                    {option.option_id || `Option ${index + 1}`}
                                </Typography>
                                <Typography variant="body2" gutterBottom sx={{ fontStyle: 'italic', marginBottom: 2 }}>
                                    {option.summary || "No summary provided."}
                                </Typography>
                                <Typography variant="subtitle2" sx={{mb: 1}}>Task Status for this Option:</Typography>
                                <List dense sx={{ width: '100%', bgcolor: 'background.paper', paddingTop: 0, maxHeight: '400px', overflowY: 'auto' }}> {/* Added scroll */}
                                    {process_tasks.map(task => {
                                        const assignmentInfo = assignmentsMap.get(task.id);
                                        const unassignedReason = unassignedReasonsMap.get(task.id);
                                        const originalActor = taskActorMap.get(task.id);
                                        let statusText = '';
                                        let statusColor = '';
                                        let fontWeight = 'normal';

                                        if (assignmentInfo) {
                                            const robotCaps = robotCapabilitiesMap.get(assignmentInfo.robot);
                                            const capabilityContext = robotCaps ? ` (Est: ${robotCaps.reach?.toFixed(1)}m Reach, ${robotCaps.payload?.toFixed(0)}kg Payload)` : '';
                                            const reasonText = assignmentInfo.reason ? assignmentInfo.reason : 'Assumed suitable capabilities.';
                                            statusText = `Automated by: ${assignmentInfo.robot}${capabilityContext} (${reasonText})`;
                                            statusColor = 'primary.main';
                                            fontWeight = 'bold';
                                        } else {
                                            if (originalActor === 'human') {
                                                statusText = `Remains Manual (${unassignedReason || 'Reason not specified'})`;
                                                statusColor = 'error.main';
                                            } else {
                                                statusText = 'Original Machine Task';
                                                statusColor = 'text.secondary';
                                            }
                                        }
                                        return (
                                            <ListItem key={`${option.option_id}-task-${task.id}`} sx={{ borderBottom: '1px solid #f0f0f0', py: 0.5 }} disablePadding>
                                                <ListItemText
                                                    primaryTypographyProps={{ sx: { fontWeight: fontWeight, color: statusColor, fontSize: '0.9rem' } }}
                                                    secondaryTypographyProps={{ sx: { fontSize: '0.75rem', color: statusColor, whiteSpace: 'pre-wrap' } }} // Wrap long reasons
                                                    primary={`Task ${task.id}: ${task.action}`}
                                                    secondary={statusText}
                                                />
                                            </ListItem>
                                        );
                                    })}
                                </List>
                            </Card>
                        );
                    })
                )}
            </Paper>

            {/* Section 3: Cost-Benefit Analysis (Effective Cost Comparison Table) */}
            <Paper elevation={2} sx={{ ...sectionPaperStyle }}>
                <Typography variant="h5" component="h3" sx={{ ...headingStyle }}>
                    Cost-Benefit Analysis (Effective Cost Comparison)
                </Typography>
                {cost_benefit_analysis.length > 0 ? (
                    cost_benefit_analysis.map((optionResult, index) => (
                        <Box key={optionResult.option_id || `cb-${index}`} sx={{ marginBottom: (index < cost_benefit_analysis.length - 1) ? 3 : 0 }}> {/* Add margin except for last */}
                            <Typography variant="h6" component="h4" gutterBottom sx={{fontWeight: 'medium'}}>
                                {optionResult.option_id || `Option ${index + 1}`} Cost Details:
                            </Typography>
                            {optionResult.robot_cost_comparison && optionResult.robot_cost_comparison.length > 0 ? (
                                <TableContainer component={Paper} variant="outlined" sx={{mb: 1}}>
                                    <Table size="small" aria-label={`cost comparison table for ${optionResult.option_id}`}>
                                        <TableHead sx={{ backgroundColor: 'action.hover' }}>
                                            <TableRow>
                                                <TableCell>Robot Used</TableCell>
                                                <TableCell align="right">Robot Eff. Cost ($/Eq. Min)</TableCell> {/* Shorter Header */}
                                                <TableCell align="right">Human Cost ($/Min)</TableCell>
                                                <TableCell align="center">Robot Cheaper?</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {optionResult.robot_cost_comparison.map((comp, compIndex) => (
                                                <TableRow key={`${optionResult.option_id}-robot-${comp.robot_name || compIndex}`}>
                                                    <TableCell component="th" scope="row">{comp.robot_name || 'N/A'}</TableCell>
                                                    <TableCell align="right">
                                                        {typeof comp.robot_effective_cost_per_human_min === 'number'
                                                            ? `$${comp.robot_effective_cost_per_human_min.toFixed(3)}`
                                                            : (comp.robot_effective_cost_per_human_min ?? 'N/A')}
                                                    </TableCell>
                                                     <TableCell align="right">
                                                        {typeof comp.human_cost_per_min === 'number'
                                                            ? `$${comp.human_cost_per_min.toFixed(3)}`
                                                            : (comp.human_cost_per_min ?? 'N/A')}
                                                    </TableCell>
                                                     <TableCell align="center" sx={{
                                                         color: comp.is_cheaper === true ? 'success.main' : (comp.is_cheaper === false ? 'error.main' : 'text.secondary'),
                                                         fontWeight: 'bold'
                                                     }}>
                                                        {comp.is_cheaper === true ? 'Yes' : (comp.is_cheaper === false ? 'No' : 'N/A')}
                                                     </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            ) : (
                                <Typography sx={{ fontStyle: 'italic', ml: 1 }}>No specific robot cost comparison available for this option.</Typography>
                            )}
                             {/* Add Divider only if it's NOT the last item */}
                             {index < cost_benefit_analysis.length - 1 && <Divider sx={{my: 2}} />}
                        </Box>
                    ))
                ) : (
                    <Typography>No cost-benefit analysis data available.</Typography>
                )}
            </Paper>

            {/* Section 4: Financial Projections Chart (NEW) */}
{userInput && process_tasks.length > 0 && automation_options.length > 0 && availableRobots && availableRobots.length > 0 && (
    <Paper elevation={2} sx={{ ...sectionPaperStyle, marginTop: 4 }}>
        <Typography variant="h5" component="h3" sx={{ ...headingStyle }}>
            Financial Projections Over Time
        </Typography>
        <Box sx={{ height: '500px', padding: { xs: 1, sm: 2 } }}>
            {/* Render the chart component, passing both data sources */}
            <TimeSeriesFinancialChart
                automationOptions={automation_options}
                processTasks={process_tasks}
                availableRobots={availableRobots}
                userInput={userInput}
                annual_projections={results.annual_projections}
            />
        </Box>
    </Paper>
)}

            {/* Section 5: Recommendation (Moved to last) */}
            <Paper elevation={2} sx={{ ...sectionPaperStyle }}>
                 <Typography variant="h5" component="h3" sx={{ ...headingStyle }}>Recommendation</Typography>
                 {recommendation.recommended_option_id ? (
                     <Box>
                         <Typography><strong>Recommended Option:</strong> {recommendation.recommended_option_id}</Typography>
                         <Typography component="div"><strong>Justification:</strong> <Box component="span" sx={{whiteSpace: 'pre-wrap'}}>{recommendation.justification}</Box></Typography> {/* Allow wrapping */}
                     </Box>
                 ) : (
                     <Typography>No recommendation provided (e.g., based on cost comparison).</Typography>
                 )}
             </Paper>

        </Box> // End overall container
    );
}

export default RoboticsResultsDisplay;