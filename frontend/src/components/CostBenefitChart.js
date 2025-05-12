import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function CostBenefitChart({ analysisResults }) {
    if (!analysisResults || analysisResults.length === 0) {
        return <div>No cost-benefit analysis data available.</div>;
    }

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Cost-Benefit Analysis Comparison',
            },
        },
         scales: { // Add scales for clarity
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Value ($ or Years)'
                }
            }
        }
    };

    const labels = analysisResults.map(res => res.option_id);

    // Prepare data, handling 'N/A' or null values
    const formatData = (key) => analysisResults.map(res => {
        const value = res[key];
        // Treat N/A or non-numeric as 0 for charting, or decide how to handle visually
        return (typeof value === 'number' && !isNaN(value)) ? value : 0;
    });


    const data = {
        labels,
        datasets: [
            {
                label: 'Total Purchase Cost ($)',
                data: formatData('total_purchase_cost'),
                backgroundColor: 'rgba(255, 99, 132, 0.5)', // Red
            },
             {
                label: 'Estimated Annual Savings ($)',
                data: formatData('estimated_annual_savings'),
                backgroundColor: 'rgba(75, 192, 192, 0.5)', // Green
            },
             {
                label: 'Payback Period (Years)',
                 // Consider using a different axis or chart type if scales differ vastly
                data: formatData('payback_period_years'),
                backgroundColor: 'rgba(53, 162, 235, 0.5)', // Blue
            },
             {
                label: 'ROI over Period (%)',
                // ROI might be better on secondary axis or separate chart
                // Multiply by 100 to show as percentage
                data: formatData('roi_over_period').map(v => v * 100),
                backgroundColor: 'rgba(255, 206, 86, 0.5)', // Yellow
            },
        ],
    };

    return <Bar options={options} data={data} />;
}

export default CostBenefitChart;