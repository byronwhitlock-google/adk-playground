import React from 'react';
import './ChatWindow.css';
import MessageList from './MessageList';
// InputBar is now directly in App.js, so it's not needed here unless there's a different layout
// import InputBar from './InputBar';

function ChatWindow({ messages }) { // Added messages prop
  return (
    <div className="chat-window">
      {/* <h2>Chat Window</h2> // Title can be optional or part of a header in App.js */}
      <MessageList messages={messages} /> {/* Pass messages to MessageList */}
      {/* InputBar will be rendered in App.js directly */}
    </div>
  );
}

export default ChatWindow;
