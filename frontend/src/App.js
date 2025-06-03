import React, { useState, useEffect } from 'react';
import './App.css'; // Assuming create-react-app created this
import { sendMessageToServer } from './services/api';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar'; // Will need to create/pass props to this

function App() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleUserInput = (text) => {
    setUserInput(text);
  };

  const handleSendMessage = async () => {
    if (userInput.trim() === '' || isLoading) {
      return;
    }

    setIsLoading(true);
    const userMessage = { id: Date.now().toString(), text: userInput, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    // Clear input after sending user's message
    const currentInput = userInput;
    setUserInput(''); // Clear input immediately

    try {
      await sendMessageToServer(
        currentInput, // Send the captured userInput
        (newMessageEvent) => {
          console.log('Received from server:', newMessageEvent);
          // Assuming newMessageEvent is the parsed JSON object from the stream
          // And it has a structure like { type: 'content_block_delta', delta: { type: 'text_delta', text: '...' } }
          // Or { type: 'message_delta', delta: { content: [{type: 'text', text: '...'}] } }
          // Or directly { content: { parts: [{text: 'some text'}] } }
          // This needs to be adapted based on the actual event structure from your backend

          let messageText = '';
          if (newMessageEvent && newMessageEvent.type === 'content_block_delta' && newMessageEvent.delta && newMessageEvent.delta.type === 'text_delta') {
            messageText = newMessageEvent.delta.text;
          } else if (newMessageEvent && newMessageEvent.delta && Array.isArray(newMessageEvent.delta.content) && newMessageEvent.delta.content[0] && newMessageEvent.delta.content[0].type === 'text') {
             // This case might be for a non-streaming part of a more complex message structure
             messageText = newMessageEvent.delta.content[0].text;
          } else if (newMessageEvent && newMessageEvent.content && Array.isArray(newMessageEvent.content.parts) && newMessageEvent.content.parts[0] && newMessageEvent.content.parts[0].text) {
            messageText = newMessageEvent.content.parts[0].text; // Example for a complete message structure
          } else if (typeof newMessageEvent.text === 'string') { // Fallback if the event is just {text: "..."}
            messageText = newMessageEvent.text;
          }


          if (messageText) {
            // Check if the last message is from the model and append content
            setMessages(prevMessages => {
              const lastMessage = prevMessages[prevMessages.length - 1];
              if (lastMessage && lastMessage.sender === 'model' && !lastMessage.isComplete) {
                return prevMessages.map((msg, index) =>
                  index === prevMessages.length - 1
                  ? { ...msg, text: msg.text + messageText }
                  : msg
                );
              } else {
                // Add new message from model
                return [...prevMessages, { id: Date.now().toString() + '-model', text: messageText, sender: 'model', isComplete: false }];
              }
            });
          } else if (newMessageEvent && (newMessageEvent.type === 'message_stop' || newMessageEvent.type === 'content_block_stop')) {
            setMessages(prevMessages => prevMessages.map(msg => msg.sender === 'model' && !msg.isComplete ? { ...msg, isComplete: true } : msg));
          }
        },
        (error) => {
          console.error('Error from server:', error);
          setMessages(prevMessages => [...prevMessages, { id: Date.now().toString(), text: 'Error: ' + error.message, sender: 'system' }]);
          setIsLoading(false);
          // setUserInput(''); // Don't clear input on error, user might want to retry
        },
        () => { // onStreamEnd callback
          console.log('Stream ended.');
          setMessages(prevMessages => prevMessages.map(msg => msg.sender === 'model' && !msg.isComplete ? { ...msg, isComplete: true } : msg));
          setIsLoading(false);
          // setUserInput(''); // Input is cleared when message is sent by user
        }
      );
    } catch (error) {
      // This catch block might be redundant if sendMessageToServer handles all its errors via onError
      console.error('Failed to send message:', error);
      setMessages(prevMessages => [...prevMessages, { id: Date.now().toString(), text: 'Failed to send message: ' + error.message, sender: 'system' }]);
      setIsLoading(false);
      // setUserInput('');
    }
  };

  return (
    <div className="App">
      <ChatWindow messages={messages} />
      <InputBar
        value={userInput}
        onChange={handleUserInput}
        onSend={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;
