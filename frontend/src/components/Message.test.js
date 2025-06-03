import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Message from './Message';

describe('Message Component', () => {
  test('renders user message correctly', () => {
    const testMessage = { id: '1', text: 'Hello user!', sender: 'user' };
    render(<Message message={testMessage} />);

    expect(screen.getByText('Hello user!')).toBeInTheDocument();
    const messageElement = screen.getByText('Hello user!').parentElement; // Get the div container
    expect(messageElement).toHaveClass('message user');
  });

  test('renders model message correctly', () => {
    const testMessage = { id: '2', text: 'Hello model!', sender: 'model' };
    render(<Message message={testMessage} />);

    expect(screen.getByText('Hello model!')).toBeInTheDocument();
    const messageElement = screen.getByText('Hello model!').parentElement;
    expect(messageElement).toHaveClass('message model');
  });

  test('renders system message correctly', () => {
    const testMessage = { id: '3', text: 'System update.', sender: 'system' };
    render(<Message message={testMessage} />);

    expect(screen.getByText('System update.')).toBeInTheDocument();
    const messageElement = screen.getByText('System update.').parentElement;
    expect(messageElement).toHaveClass('message system');
  });

  test('does not render if message prop is null', () => {
    const { container } = render(<Message message={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('does not render if message prop is undefined', () => {
    const { container } = render(<Message message={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});
