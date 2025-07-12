#!/bin/bash
# deploy.sh - Complete deployment script

echo "🚀 Smart Document Assistant Deployment Script"
echo "==========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# 1. Initialize Git repository
echo "📁 Initializing Git repository..."
git init
git add .
git commit -m "Initial commit - Smart Document Assistant"

# 2. Create GitHub repository
echo "📤 Creating GitHub repository..."
echo "Please go to https://github.com/new and create a new repository"
echo "Repository name suggestion: smart-document-assistant"
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): " REPO_URL

git remote add origin $REPO_URL
git push -u origin main

# 3. Deploy Backend to Render
echo "🔧 Deploying Backend to Render.com..."
echo "Steps:"
echo "1. Go to https://render.com"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Configure:"
echo "   - Name: smart-doc-assistant-api"
echo "   - Root Directory: backend"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: python main.py"
echo "5. Add environment variable:"
echo "   - Key: GEMINI_API_KEY"
echo "   - Value: [Your Gemini API Key]"
echo ""
read -p "Press Enter when backend is deployed. Enter the backend URL: " BACKEND_URL

# 4. Update frontend with backend URL
echo "🎨 Updating frontend configuration..."
echo "REACT_APP_API_URL=$BACKEND_URL" > frontend/.env.production

# 5. Deploy Frontend to Vercel
echo "🌐 Deploying Frontend to Vercel..."
cd frontend

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm i -g vercel
fi

echo "Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Deployment Complete!"
echo "========================"
echo "Your Smart Document Assistant is now live!"
echo ""
echo "📝 Next Steps:"
echo "1. Upload a PDF or Excel file"
echo "2. Ask questions about your document"
echo "3. Share with your team!"
echo ""
echo "🔒 Security Tips:"
echo "- Keep your Gemini API key secret"
echo "- Consider adding authentication for production use"
echo "- Monitor your API usage in Google AI Studio"
