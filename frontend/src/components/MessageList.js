import React, { useEffect, useRef } from 'react';
import './MessageList.css';
import Message from './Message';

function MessageList({ messages }) { // Added messages prop
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]); // Scroll to bottom whenever messages change

  return (
    <div className="message-list">
      {messages && messages.map(msg => ( // Check if messages is not undefined
        <Message key={msg.id} message={msg} /> // Pass the whole message object
      ))}
      <div ref={messagesEndRef} /> {/* Element to scroll to */}
    </div>
  );
}

export default MessageList;
