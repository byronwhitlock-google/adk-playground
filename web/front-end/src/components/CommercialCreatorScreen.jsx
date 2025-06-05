import React, { useState, useRef } from 'react';
import { ArrowUpTrayIcon, PhotoIcon } from '@heroicons/react/24/solid'; // Example icons

function CommercialCreatorScreen() {
  const [description, setDescription] = useState('');
  const [images, setImages] = useState([]); // Array of { file: File, previewUrl: string, prompt: string }
  const fileInputRef = useRef(null);

  const handleDescriptionChange = (event) => {
    setDescription(event.target.value);
  };

  const handleImageUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    const newImages = files.map(file => ({
      file,
      previewUrl: URL.createObjectURL(file),
      prompt: ''
    }));
    setImages(prevImages => [...prevImages, ...newImages]);
  };

  const handlePromptChange = (index, prompt) => {
    setImages(prevImages =>
      prevImages.map((image, i) =>
        i === index ? { ...image, prompt } : image
      )
    );
  };

  const handleSubmit = () => {
    console.log('Commercial Description:', description);
    console.log('Images with Prompts:', images.map(img => ({ fileName: img.file.name, prompt: img.prompt, size: img.file.size, type: img.file.type })));
    // For actual file objects, you might log: images.map(img => ({ file: img.file, prompt: img.prompt }))
    // However, logging the full File object might be too verbose for console.
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white shadow-md rounded-lg p-6 sm:p-8">
        <header className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 text-center">
            Tell me about your commercial
          </h1>
        </header>

        <section className="space-y-6">
          <div>
            <label htmlFor="commercial-description" className="block text-sm font-medium text-gray-700 mb-1">
              Commercial Description
            </label>
            <textarea
              id="commercial-description"
              value={description}
              onChange={handleDescriptionChange}
              placeholder="Describe the product, the target audience, the tone and style, and any key messages..."
              rows="6"
              className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-y"
            />
          </div>

          {images.length > 0 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-700">Image Previews & Prompts</h3>
              <div className="flex flex-row gap-4 overflow-x-auto pb-4">
                {images.map((image, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3 shadow-sm w-full max-w-xs flex-shrink-0">
                    <img
                      src={image.previewUrl}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-40 object-cover rounded-md mb-2"
                      onLoad={() => URL.revokeObjectURL(image.previewUrl)} // Clean up object URL after load
                    />
                    <input
                      type="text"
                      value={image.prompt}
                      onChange={(e) => handlePromptChange(index, e.target.value)}
                      placeholder="Enter prompt..."
                      className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-3">Upload Images</h2>
            <button
              type="button"
              onClick={handleImageUploadClick}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg inline-flex items-center justify-center space-x-2 transition duration-150 ease-in-out"
            >
              <ArrowUpTrayIcon className="h-6 w-6" />
              <span>Upload Images</span>
            </button>
            <input
              type="file"
              multiple
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept="image/*"
            />
          </div>

          <div className="pt-6">
            <button
              type="button"
              onClick={handleSubmit}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition duration-150 ease-in-out"
            >
              Let's Get Started!
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default CommercialCreatorScreen;
