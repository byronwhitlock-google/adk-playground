import React from 'react';
import './Message.css';

function Message({ message }) { // Changed props to accept a message object
  if (!message) return null; // Handle null message case

  const { text, sender } = message;

  // Add a class for system messages if you have them
  const messageClass = `message ${sender} ${sender === 'system' ? 'system-message' : ''}`;

  return (
    <div className={messageClass}>
      <p>{text}</p>
    </div>
  );
}

export default Message;
