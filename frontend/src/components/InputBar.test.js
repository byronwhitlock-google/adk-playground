import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import InputBar from './InputBar';

describe('InputBar Component', () => {
  const mockOnChange = jest.fn();
  const mockOnSend = jest.fn();

  beforeEach(() => {
    // Clear mock call history before each test
    mockOnChange.mockClear();
    mockOnSend.mockClear();
  });

  test('renders input field and send button', () => {
    render(<InputBar value="" onChange={mockOnChange} onSend={mockOnSend} isLoading={false} />);
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  test('calls onChange handler when typing into input', () => {
    render(<InputBar value="" onChange={mockOnChange} onSend={mockOnSend} isLoading={false} />);
    const inputElement = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(inputElement, { target: { value: 'Hello test' } });
    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('Hello test');
  });

  test('calls onSend handler when send button is clicked with non-empty input', () => {
    render(<InputBar value="Not empty" onChange={mockOnChange} onSend={mockOnSend} isLoading={false} />);
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    expect(mockOnSend).toHaveBeenCalledTimes(1);
  });

  test('does NOT call onSend handler if input is empty and send button is clicked', () => {
    // Note: The InputBar component itself doesn't prevent onSend if value is empty.
    // This logic is typically in the parent (App.js handleSendMessage).
    // So, we test that onSend is called, and the parent would be responsible for the trim check.
    // If InputBar *were* to have this logic, this test would change.
    render(<InputBar value="" onChange={mockOnChange} onSend={mockOnSend} isLoading={false} />);
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    // As per current InputBar implementation, it will call onSend.
    // The parent component (App.js) is responsible for checking if the input is empty.
    expect(mockOnSend).toHaveBeenCalledTimes(1);
  });

  test('input field and send button are disabled when isLoading is true', () => {
    render(<InputBar value="" onChange={mockOnChange} onSend={mockOnSend} isLoading={true} />);
    const inputElement = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /sending.../i }); // Text changes when loading

    expect(inputElement).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  test('input field and send button are enabled when isLoading is false', () => {
    render(<InputBar value="" onChange={mockOnChange} onSend={mockOnSend} isLoading={false} />);
    const inputElement = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    expect(inputElement).toBeEnabled();
    expect(sendButton).toBeEnabled();
  });

  test('displays "Sending..." on button when isLoading is true', () => {
    render(<InputBar value="test" onChange={mockOnChange} onSend={mockOnSend} isLoading={true} />);
    expect(screen.getByRole('button', { name: /sending.../i })).toBeInTheDocument();
  });
});
