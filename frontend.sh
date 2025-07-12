#!/bin/bash
# Complete Frontend Setup Script

# Create frontend directory
mkdir -p smart-doc-assistant/frontend
cd smart-doc-assistant/frontend

# Create package.json
cat > package.json << 'EOF'
{
  "name": "smart-doc-assistant",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.263.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "react-scripts": "5.0.1",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

# Create public/index.html
mkdir -p public
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Smart Document Assistant - Upload and analyze PDFs and Excel files" />
    <title>Smart Document Assistant</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create src directory and files
mkdir -p src

# Create src/index.js
cat > src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Create src/index.css
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
EOF

# Create src/App.js
cat > src/App.js << 'EOF'
import React, { useState } from 'react';
import { Upload, FileText, MessageSquare, Send, Loader2, Trash2, FileSpreadsheet, AlertCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function App() {
  const [file, setFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [documentInfo, setDocumentInfo] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const validTypes = ['.pdf', '.xlsx', '.xls'];
    const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
      setError('Please upload a PDF or Excel file');
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setFile(selectedFile);
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      
      setSessionId(data.session_id);
      setDocumentInfo({
        filename: data.filename,
        docType: data.doc_type,
        contentLength: data.content_length
      });
      setMessages([{
        type: 'system',
        content: data.initial_summary
      }]);
    } catch (error) {
      setError('Error uploading file: ' + error.message);
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const userMessage = inputMessage;
    setInputMessage('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: userMessage
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { type: 'assistant', content: data.answer }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Error: ' + error.message 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSession = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_URL}/sessions/${sessionId}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.error('Error deleting session:', error);
      }
    }
    
    setFile(null);
    setSessionId(null);
    setMessages([]);
    setDocumentInfo(null);
    setError(null);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Smart Document Assistant</h1>
                <p className="text-sm text-gray-500">Upload PDF or Excel files and ask questions</p>
              </div>
            </div>
            {documentInfo && (
              <button
                onClick={clearSession}
                className="flex items-center space-x-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                <span>Clear Session</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-6xl mx-auto w-full px-4 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
            <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-4 py-6 overflow-hidden">
        {!sessionId ? (
          // Upload Screen
          <div className="flex items-center justify-center h-full">
            <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
              <div className="text-center mb-6">
                <Upload className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Upload Your Document</h2>
                <p className="text-gray-600">
                  Upload a PDF or Excel file to start asking questions about it
                </p>
              </div>
              
              <label className="block">
                <input
                  type="file"
                  accept=".pdf,.xlsx,.xls"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={isUploading}
                />
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-500 cursor-pointer transition-colors">
                  {isUploading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                      <span>Processing document...</span>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-gray-600">Click to browse or drag and drop</p>
                      <p className="text-sm text-gray-500 mt-1">PDF or Excel files only (max 10MB)</p>
                    </div>
                  )}
                </div>
              </label>

              <div className="mt-6 space-y-2">
                <h3 className="font-medium text-gray-700">Example questions you can ask:</h3>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>Summarize the financial highlights of Q2</li>
                  <li>Which suppliers had delayed payments over 30 days?</li>
                  <li>What were the top 5 expenses last month?</li>
                  <li>Show me the revenue breakdown by category</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          // Chat Interface
          <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
            {/* Document Info Bar */}
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center space-x-2">
              {documentInfo.docType === 'PDF' ? (
                <FileText className="h-5 w-5 text-red-600" />
              ) : (
                <FileSpreadsheet className="h-5 w-5 text-green-600" />
              )}
              <span className="font-medium">{documentInfo.filename}</span>
              <span className="text-sm text-gray-500">• {documentInfo.docType}</span>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-3xl px-4 py-3 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-100 text-red-700'
                        : message.type === 'system'
                        ? 'bg-gray-100 text-gray-700'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {message.type === 'system' && (
                      <div className="flex items-center space-x-2 mb-1">
                        <MessageSquare className="h-4 w-4" />
                        <span className="text-sm font-medium">Document Summary</span>
                      </div>
                    )}
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-3 rounded-lg">
                    <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask a question about your document..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
EOF

# Create tailwind.config.js
cat > tailwind.config.js << 'EOF'
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

# Create postcss.config.js
cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# Create .env.example
cat > .env.example << 'EOF'
REACT_APP_API_URL=http://localhost:8000
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
node_modules
/.pnp
.pnp.js
/coverage
/build
.DS_Store
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
EOF

# Create README.md
cat > README.md << 'EOF'
# Smart Document Assistant Frontend

## Setup
1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env`
3. Update `REACT_APP_API_URL` if needed
4. Run: `npm start`

## Build for production
`npm run build`
EOF

echo "Frontend setup complete!"
