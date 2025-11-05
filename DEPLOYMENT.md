# Deployment Guide

This guide will help you deploy the Job Aggregator to both GitHub Pages and Vercel.

## Prerequisites

- GitHub account
- Git installed locally
- (Optional) Vercel account

## Step 1: Initialize Git Repository

If you haven't already initialized git in this directory:

```bash
cd "/Users/rohitkota/Job Aggregator"
git init
git add .
git commit -m "Initial commit: Job Aggregator MVP"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `job-aggregator`)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Copy the repository URL

## Step 3: Push to GitHub

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/job-aggregator.git

# Push to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` and `job-aggregator` with your actual GitHub username and repo name.

## Step 4: Deploy to GitHub Pages

### Option A: Using GitHub Pages Settings (Recommended)

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select:
   - **Deploy from a branch**
   - Branch: `main`
   - Folder: `/frontend`
5. Click **Save**
6. GitHub will deploy your site to: `https://YOUR_USERNAME.github.io/job-aggregator/`

### Option B: Using GitHub Actions (Alternative)

If you prefer GitHub Actions to deploy, we can create a workflow file that builds and deploys.

## Step 5: Configure GitHub Actions Permissions

For the daily scraper to work, you need to enable write permissions:

1. Go to repository **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select:
   - **Read and write permissions**
   - Check **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

## Step 6: Test GitHub Actions Workflow

1. Go to **Actions** tab in your repository
2. You should see "Daily Job Scraper" workflow
3. Click **Run workflow** to test it manually
4. It will:
   - Run the scraper
   - Update jobs.json
   - Commit and push changes

## Step 7: Deploy to Vercel (Optional)

### Option A: GitHub Integration (Recommended)

1. Go to https://vercel.com
2. Sign up/login with GitHub
3. Click **Add New Project**
4. Import your GitHub repository
5. Vercel will auto-detect `vercel.json`
6. Click **Deploy**
7. Your site will be live at: `https://job-aggregator.vercel.app`

### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd "/Users/rohitkota/Job Aggregator"
vercel
```

## Post-Deployment Checklist

- [ ] GitHub Pages site is live
- [ ] Frontend loads jobs.json correctly
- [ ] Search/filter functionality works
- [ ] GitHub Actions workflow runs successfully
- [ ] Jobs.json updates daily (check after 24 hours)
- [ ] (Optional) Vercel deployment works

## Troubleshooting

### GitHub Pages shows 404

- Make sure `/frontend` folder is set as source
- Check that `frontend/.nojekyll` exists
- Verify `frontend/jobs.json` exists

### GitHub Actions fails

- Check that workflow permissions are set to "Read and write"
- Verify `jobs.json` is not in `.gitignore`
- Check workflow logs in Actions tab

### Frontend can't load jobs.json

- Make sure `jobs.json` exists in `frontend/` directory
- Check browser console for CORS errors
- Verify file path in `app.js` matches deployment structure

### Scraper returns 0 jobs

- Check internet connection
- Verify config.json has active sources
- Some sites may block scrapers (403 errors) - this is normal

## Updating the Site

After deployment, jobs will update automatically via GitHub Actions daily at 2 AM UTC.

To manually trigger an update:
1. Go to **Actions** tab
2. Click **Daily Job Scraper**
3. Click **Run workflow**
4. Click **Run workflow** button

## Custom Domain (Optional)

### GitHub Pages
1. Add `CNAME` file in `frontend/` with your domain
2. Configure DNS records as per GitHub Pages instructions

### Vercel
1. Go to project settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed

