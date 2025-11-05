#!/bin/bash
# Quick deployment script
# Run this after setting up your GitHub repo

echo "🚀 Job Aggregator Deployment Helper"
echo "===================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Job Aggregator MVP"
    echo "✅ Git initialized"
else
    echo "✅ Git repository already initialized"
fi

# Check if remote exists
if git remote get-url origin &>/dev/null; then
    echo "✅ Remote repository configured"
    REMOTE_URL=$(git remote get-url origin)
    echo "   Remote: $REMOTE_URL"
else
    echo "⚠️  No remote repository configured"
    echo ""
    echo "To set up remote:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/job-aggregator.git"
    echo "  git push -u origin main"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Create GitHub repository at: https://github.com/new"
echo "2. Add remote: git remote add origin <your-repo-url>"
echo "3. Push: git push -u origin main"
echo "4. Enable GitHub Pages:"
echo "   - Go to Settings → Pages"
echo "   - Source: Deploy from branch 'main', folder '/frontend'"
echo "5. Enable GitHub Actions permissions:"
echo "   - Settings → Actions → General"
echo "   - Workflow permissions: Read and write"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"

