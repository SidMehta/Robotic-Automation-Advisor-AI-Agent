import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import Typography from '@mui/material/Typography';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Chart colors
const G_CHART_COLORS = [
  'rgba(54, 162, 235, 0.7)',   // Blue
  'rgba(255, 99, 132, 0.7)',   // Red
  'rgba(75, 192, 192, 0.7)',   // Teal
  'rgba(255, 205, 86, 0.7)',   // Yellow
  'rgba(153, 102, 255, 0.7)',  // Purple
  'rgba(255, 159, 64, 0.7)'    // Orange
];
const BASELINE_COLOR_BG = 'rgba(100, 100, 100, 0.7)';
const BASELINE_COLOR_BORDER = 'rgb(100, 100, 100)';

function TimeSeriesFinancialChart({ userInput, annual_projections = [] }) {
  // Basic validation
  const isValidNumber = (val) => typeof val === 'number' && !isNaN(val);
  if (
    !userInput ||
    !isValidNumber(userInput.depreciation_years) ||
    !Array.isArray(annual_projections)
  ) {
    return (
      <Typography sx={{ fontStyle: 'italic', textAlign: 'center', p: 1 }}>
        No financial projection data available. Try running analysis again.
      </Typography>
    );
  }

  // Build X-axis (Year 0 … Year T)
  const T_years = Math.floor(userInput.depreciation_years);
  const years = Array.from({ length: T_years + 1 }, (_, i) => `Year ${i}`);

  // Prepare datasets
  const datasets = [];

  // Baseline: “No Automation” human-only cost
  if (
    annual_projections.length > 0 &&
    Array.isArray(annual_projections[0].baseline_cumulative_costs_by_year)
  ) {
    datasets.push({
      label: 'No Automation (Total Human Cost)',
      data: annual_projections[0].baseline_cumulative_costs_by_year,
      backgroundColor: BASELINE_COLOR_BG,
      borderColor: BASELINE_COLOR_BORDER,
      borderWidth: 1
    });
  }

  // Automation options: strip Year 0 CAPEX, plot amortized cost only
  annual_projections.forEach((proj, idx) => {
    const raw = proj.cumulative_costs_by_year || [];
    if (raw.length === 0) {
      console.warn(`No cumulative cost data for ${proj.option_id}`);
      return;
    }
    const initialCap = raw[0] || 0;
    const amortized = raw.map((v, i) => (i === 0 ? 0 : v - initialCap));

    const colorIndex = idx % G_CHART_COLORS.length;
    datasets.push({
      label: `${proj.option_id} (Total Cost)`,
      data: amortized,
      backgroundColor: G_CHART_COLORS[colorIndex],
      borderColor: G_CHART_COLORS[colorIndex].replace('0.7', '1'),
      borderWidth: 1
    });

    console.log(`Chart data for ${proj.option_id}:`, amortized);
  });

  const chartData = { labels: years, datasets };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: {
        display: true,
        text: `Total Cumulative Cost Over ${T_years} Years`,
        font: { size: 16 }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (ctx) => {
            let lbl = ctx.dataset.label || '';
            const y = ctx.parsed.y;
            if (y != null && !isNaN(y)) {
              lbl +=
                ': ' +
                new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  maximumFractionDigits: 0
                }).format(y);
            } else {
              lbl += ' N/A';
            }
            return lbl;
          }
        }
      }
    },
    scales: {
      x: { title: { display: true, text: 'Year' } },
      y: {
        title: { display: true, text: 'Total Cumulative Cost ($)' },
        beginAtZero: true,
        ticks: {
          callback: (val) => `$${val.toLocaleString()}`
        }
      }
    }
  };

  // If no numeric data, show message
  const hasData = datasets.some((ds) =>
    Array.isArray(ds.data) && ds.data.some((n) => typeof n === 'number')
  );
  if (!hasData) {
    return (
      <Typography sx={{ fontStyle: 'italic', textAlign: 'center', p: 1 }}>
        No plottable data for cost projections (check input data and robot metadata).
      </Typography>
    );
  }

  // Finally render
  return <Bar options={chartOptions} data={chartData} />;
}

export default TimeSeriesFinancialChart;
