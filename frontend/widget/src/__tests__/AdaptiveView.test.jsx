import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';
import { A2UIRenderer } from '../a2ui/renderer';

describe('A2UIRenderer Component (Hybrid UI)', () => {
  const mockData = {
    data_view: {
      text: "Professional Skills",
      layout: "grid",
      items: [
        { "Skill": "Python", "Level": "95%" },
        { "Skill": "JavaScript", "Level": "90%" }
      ]
    }
  };

  it('renders the title and data items correctly', () => {
    render(<A2UIRenderer data={mockData} />);
    
    expect(screen.getByText('Professional Skills')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
  });

  it('displays proficiency levels from the adaptive grid', () => {
    render(<A2UIRenderer data={mockData} />);
    
    // Check if the proficiency values are rendered
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
  });

  it('applies the correct layout class for list mode', () => {
    const listData = {
      data_view: { ...mockData.data_view, layout: "list" }
    };
    render(<A2UIRenderer data={listData} />);
    
    // The title sibling or parent wrapper should contain the component with correct class
    const container = screen.getByText('Professional Skills').parentElement.querySelector('.a2ui-adaptive-view');
    expect(container).toHaveClass('list');
  });

  it('renders correctly without a title', () => {
    const headlessData = {
      data_view: { ...mockData.data_view, text: "" }
    };
    render(<A2UIRenderer data={headlessData} />);
    
    expect(screen.queryByText('Professional Skills')).not.toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
  });
});
