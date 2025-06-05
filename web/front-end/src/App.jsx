import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomeScreen from './components/HomeScreen';
import CommercialCreatorScreen from './components/CommercialCreatorScreen';
import './App.css'; // Keep if it has any global styles you want, or remove
// Ensure index.css (where Tailwind is imported) is imported in main.jsx

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100"> {/* Apply global background */}
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/create" element={<CommercialCreatorScreen />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
