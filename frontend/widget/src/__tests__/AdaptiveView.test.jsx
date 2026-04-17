import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';
import { AdaptiveView } from '../App';

describe('AdaptiveView Component', () => {
  const mockData = {
    text: "Professional Skills",
    layout: "grid",
    items: [
      { "Skill": "Python", "Level": "95%" },
      { "Skill": "JavaScript", "Level": "90%" }
    ]
  };

  it('renders the title and items correctly', () => {
    render(<AdaptiveView data_view={mockData} />);
    
    expect(screen.getByText('Professional Skills')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
  });

  it('correctly identifies and displays proficiency levels as percentages', () => {
    render(<AdaptiveView data_view={mockData} />);
    
    // Check if the proficiency values are rendered
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
  });

  it('falls back gracefully to list layout', () => {
    const listData = { ...mockData, layout: "list" };
    render(<AdaptiveView data_view={listData} />);
    
    const container = screen.getByText('Professional Skills').closest('.adaptive-view');
    expect(container).toHaveClass('layout-list');
  });

  it('renders correctly without a title', () => {
    const headlessData = { ...mockData, text: "" };
    render(<AdaptiveView data_view={headlessData} />);
    
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
  });
});
