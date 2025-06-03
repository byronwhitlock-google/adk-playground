import React from 'react'; // Removed useState as value is controlled by parent
import './InputBar.css';

function InputBar({ value, onChange, onSend, isLoading }) { // Added props

  const handleSubmit = (e) => {
    e.preventDefault();
    onSend(); // Call onSend passed from App.js
  };

  const handleInputChange = (e) => {
    onChange(e.target.value); // Call onChange passed from App.js
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value} // Use value from props
        onChange={handleInputChange} // Use handler from props
        placeholder="Type a message..."
        disabled={isLoading} // Disable input if isLoading
      />
      <button type="submit" disabled={isLoading}> {/* Disable button if isLoading */}
        {isLoading ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
}

export default InputBar;
