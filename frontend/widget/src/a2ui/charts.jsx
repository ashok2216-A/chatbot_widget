import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from 'recharts';

/**
 * A2Chart Component
 * Supports 'bar', 'pie', and 'line' types.
 * Data format: Array of objects, e.g., [{ name: 'Page A', value: 400 }]
 */
export function A2Chart({ type = 'bar', data = [], title, colors }) {
  const chartType = type.toLowerCase();
  
  // Default color palette using CSS variables or fallback theme colors
  const defaultColors = [
    'var(--cw-accent)',
    'var(--cw-teal)',
    '#F59E0B', // Orange
    '#EC4899', // Pink
    '#3B82F6', // Blue
    '#10B981', // Green
  ];
  
  const activeColors = colors || defaultColors;

  const renderChart = () => {
    switch (chartType) {
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={activeColors[index % activeColors.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'var(--cw-surface)', 
                borderColor: 'var(--cw-border)',
                borderRadius: '8px',
                color: 'var(--cw-text)'
              }} 
            />
            <Legend verticalAlign="bottom" height={36}/>
          </PieChart>
        );
      case 'line':
        return (
          <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--cw-border)" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="var(--cw-text-dim)" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              stroke="var(--cw-text-dim)" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'var(--cw-surface)', 
                borderColor: 'var(--cw-border)',
                borderRadius: '8px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="var(--cw-accent)" 
              strokeWidth={3} 
              dot={{ r: 4, fill: 'var(--cw-accent)', strokeWidth: 2, stroke: 'var(--cw-surface)' }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        );
      case 'bar':
      default:
        return (
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--cw-border)" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="var(--cw-text-dim)" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              stroke="var(--cw-text-dim)" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip 
              cursor={{ fill: 'var(--cw-border)', opacity: 0.4 }}
              contentStyle={{ 
                backgroundColor: 'var(--cw-surface)', 
                borderColor: 'var(--cw-border)',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey="value" fill="var(--cw-accent)" radius={[4, 4, 0, 0]} />
          </BarChart>
        );
    }
  };

  return (
    <div className="a2ui-chart-container">
      {title && <h4 className="a2ui-chart-title">{title}</h4>}
      <div className="a2ui-chart-wrapper">
        <ResponsiveContainer width="100%" height={200}>
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
