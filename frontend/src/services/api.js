// Placeholder values
const APP_NAME = "chat_app";
const USER_ID = "user_1";
const SESSION_ID = "session_1";

export async function sendMessageToServer(message, onMessageReceived, onError, onStreamEnd) { // Added onStreamEnd
  try {
    const response = await fetch('/run_sse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream' // Important to indicate we expect a stream
      },
      body: JSON.stringify({
        app_name: APP_NAME,
        user_id: USER_ID,
        session_id: SESSION_ID,
        message: {
          human_message: message,
        },
        streaming: true,
      }),
    });

    if (!response.ok) {
      // Handle HTTP errors like 4xx, 5xx
      const errorBody = await response.text();
      onError(new Error(`HTTP error ${response.status}: ${errorBody || response.statusText}`));
      return;
    }

    if (!response.body) {
      onError(new Error('Response body is null.'));
      if (onStreamEnd) onStreamEnd(); // Call onStreamEnd even if body is null
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // Process any remaining data in the buffer before breaking
        if (buffer.trim().length > 0) {
            // Attempt to process any final, potentially incomplete, message.
            // This might be risky if the stream ends mid-message.
            // Consider if this is robust enough for your specific SSE format.
            const lines = buffer.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonString = line.substring(6);
                        if (jsonString) { // Ensure jsonString is not empty
                             const event = JSON.parse(jsonString);
                             onMessageReceived(event);
                        }
                    } catch (e) {
                        // Log parsing error but don't necessarily call onError for every partial message
                        // as more data might be coming or it might be the end of a valid message.
                        console.error('Error parsing JSON from SSE stream:', e);
                    }
                }
            }
        }
        if (onStreamEnd) onStreamEnd(); // Call onStreamEnd when stream is finished
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split('\n');

      // Keep the last (potentially incomplete) line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonString = line.substring(6);
            if (jsonString.trim()) { // Ensure jsonString is not empty and not just whitespace
                const event = JSON.parse(jsonString);
                onMessageReceived(event);
            }
          } catch (e) {
            // It's possible to receive a partial JSON string if a chunk ends mid-event.
            // We log the error, but the current incomplete line is put back into the buffer
            // by `buffer = lines.pop() || '';` and `buffer += decoder.decode...`
            // to be completed by the next chunk.
            // If this error persists with complete messages, then it's a true parsing error.
            console.error('Error parsing JSON from SSE stream chunk:', e, "Line:", line);
            // Decide if this is critical enough to call onError
            // onError(new Error(`Error parsing JSON: ${e.message}`));
          }
        } else if (line.trim() === '' && buffer.trim().startsWith('data:')) {
            // This case handles when a complete data message (ending with \n\n)
            // is split across chunks, and the current chunk ends with \n
            // The next line would be empty, signaling the end of an event.
            // The buffer at this point would have "data: {...}"
            // This logic is simplified; a more robust parser might be needed.
        }
      }
    }

  } catch (error) {
    // Handle network errors or errors from reader.read()
    console.error('Error in sendMessageToServer:', error);
    onError(error);
    if (onStreamEnd) onStreamEnd(); // Call onStreamEnd on error too
  }
}
