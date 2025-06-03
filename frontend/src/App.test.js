import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { sendMessageToServer } from './services/api'; // To mock this

// Mock the ResizeObserver
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserver;


// Mock the api service
jest.mock('./services/api', () => ({
  sendMessageToServer: jest.fn(),
}));

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = jest.fn();

describe('App Component Interaction Tests', () => {
  beforeEach(() => {
    // Clear mock calls and implementation before each test
    sendMessageToServer.mockClear();
    // Provide a default mock implementation that simulates an async call
    // and immediately calls onStreamEnd and resolves.
    sendMessageToServer.mockImplementation(async (message, onMessageReceived, onError, onStreamEnd) => {
      // Simulate a model response if needed for specific tests, otherwise just end.
      // Example: onMessageReceived({ type: 'content_block_delta', delta: { type: 'text_delta', text: 'Model response' } });
      if (onStreamEnd) {
        onStreamEnd();
      }
      return Promise.resolve();
    });
  });

  test('allows user to send a message and see it displayed, and calls api', async () => {
    render(<App />);

    const inputElement = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Simulate typing a message
    fireEvent.change(inputElement, { target: { value: 'Hello World' } });
    expect(inputElement.value).toBe('Hello World');

    // Simulate clicking send
    fireEvent.click(sendButton);

    // Check if the user's message appears on screen
    // It might take a moment for the state to update and re-render
    await waitFor(() => {
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });

    // Check that the input is cleared after sending
    expect(inputElement.value).toBe('');

    // Check if sendMessageToServer was called correctly
    expect(sendMessageToServer).toHaveBeenCalledTimes(1);
    expect(sendMessageToServer).toHaveBeenCalledWith(
      'Hello World', // The message sent
      expect.any(Function), // onMessageReceived callback
      expect.any(Function), // onError callback
      expect.any(Function)  // onStreamEnd callback
    );
  });

  test('displays model message when onMessageReceived is called', async () => {
    sendMessageToServer.mockImplementation(async (message, onMessageReceived, onError, onStreamEnd) => {
      onMessageReceived({ type: 'content_block_delta', delta: { type: 'text_delta', text: 'Model says hello!' } });
      if (onStreamEnd) {
        onStreamEnd();
      }
      return Promise.resolve();
    });

    render(<App />);

    fireEvent.change(screen.getByPlaceholderText('Type a message...'), { target: { value: 'User query' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText('User query')).toBeInTheDocument(); // User message
    });

    await waitFor(() => {
      expect(screen.getByText('Model says hello!')).toBeInTheDocument(); // Model message
    });
  });

  test('displays error message when onError is called', async () => {
    const MOCK_ERROR_MESSAGE = 'Failed to connect';
    sendMessageToServer.mockImplementation(async (message, onMessageReceived, onError, onStreamEnd) => {
      onError(new Error(MOCK_ERROR_MESSAGE));
      // No onStreamEnd call here as per typical error flow leading to isLoading=false
      return Promise.resolve(); // Or Promise.reject(new Error(MOCK_ERROR_MESSAGE));
    });

    render(<App />);

    fireEvent.change(screen.getByPlaceholderText('Type a message...'), { target: { value: 'Test error' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText('Test error')).toBeInTheDocument(); // User message
    });

    await waitFor(() => {
      // The error message prepends "Error: "
      expect(screen.getByText(`Error: ${MOCK_ERROR_MESSAGE}`)).toBeInTheDocument();
    });

    //isLoading should be false
     await waitFor(() => {
      expect(screen.getByRole('button', { name: /send/i })).not.toBeDisabled();
    });
  });

  test('handles multiple streamed messages correctly', async () => {
    sendMessageToServer.mockImplementation(async (message, onMessageReceived, onError, onStreamEnd) => {
      onMessageReceived({ type: 'content_block_delta', delta: { type: 'text_delta', text: 'Part 1. ' } });
      onMessageReceived({ type: 'content_block_delta', delta: { type: 'text_delta', text: 'Part 2.' } });
      if (onStreamEnd) {
        onStreamEnd();
      }
      return Promise.resolve();
    });

    render(<App />);
    fireEvent.change(screen.getByPlaceholderText('Type a message...'), { target: { value: 'Stream test' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText('Stream test')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText('Part 1. Part 2.')).toBeInTheDocument();
    });
  });

});
