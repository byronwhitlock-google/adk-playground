import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightIcon } from '@heroicons/react/24/solid'; // Example icon

function HomeScreen() {
  const navigate = useNavigate();

  const handleCreateCommercial = () => {
    navigate('/create');
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white shadow-md rounded-lg text-center">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Commercial Creation Tool</h1>
        <button
          onClick={handleCreateCommercial}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg inline-flex items-center space-x-2 transition duration-150 ease-in-out"
        >
          <span>Create a Commercial</span>
          <ArrowRightIcon className="h-5 w-5" />
        </button>
        <p className="mt-4 text-sm text-gray-600">Click the button above to start crafting your next commercial.</p>
      </div>
    </div>
  );
}

export default HomeScreen;
