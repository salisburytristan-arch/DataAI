# Deploy ArcticCodex Chat to Vercel

## Overview

Your chat system has two parts:
- **Backend (Studio Server)**: Runs on Fly.io with vault + LLM
- **Frontend (Next.js site)**: Runs on Vercel

## Step 1: Deploy Backend to Fly.io

```bash
# From root directory
python run_studio.py fly
```

This creates: `https://arcticcodex-studio.fly.dev`

## Step 2: Deploy Frontend to Vercel

### Option A: Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to arctic-site
cd arctic-site

# Deploy
vercel

# Follow prompts:
# - Link to existing project or create new
# - Set environment variables (see below)
```

### Option B: Vercel Dashboard

1. Go to https://vercel.com
2. Import Git repository
3. Select `arctic-site` folder as root
4. Add environment variables (see below)
5. Deploy

## Step 3: Configure Environment Variables

In Vercel dashboard or CLI, set:

```bash
NEXT_PUBLIC_API_URL=https://arcticcodex-studio.fly.dev
NEXT_PUBLIC_LLM_ENDPOINT=https://arcticcodex-studio.fly.dev
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

## Step 4: Test Deployment

Visit your Vercel URL:
- Chat page: `https://your-domain.vercel.app/chat`
- API health: `https://your-domain.vercel.app/api/health`

The frontend will proxy requests to your Fly backend.

## Local Development

```bash
# Terminal 1: Start Studio backend
cd D:\ArcticCodex - AGI
.\start_studio.ps1

# Terminal 2: Start Next.js frontend
cd arctic-site
npm run dev
```

Update `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

Visit: http://localhost:3000/chat

## Architecture

```
User Browser
    ↓
Vercel (Next.js Frontend)
    ↓ API Proxy
Fly.io (Studio Server)
    ├─ Vault (230k chunks)
    └─ Mistral 7B LLM
```

## Vercel CLI Commands

```bash
# Deploy to production
vercel --prod

# Deploy to preview
vercel

# View logs
vercel logs

# List deployments
vercel ls

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
```

## Custom Domain

In Vercel dashboard:
1. Go to Project Settings → Domains
2. Add custom domain: `arcticcodex.com`
3. Update DNS records as shown
4. Wait for SSL certificate

Update environment:
```
NEXT_PUBLIC_SITE_URL=https://arcticcodex.com
```

## Troubleshooting

### "API not responding"
- Check Fly backend is running: `fly status`
- Check environment variable points to correct URL
- Test directly: `curl https://arcticcodex-studio.fly.dev/api/health`

### "CORS errors"
Studio server allows all origins by default. If you see CORS errors, check the Studio server logs: `fly logs`

### "Chat not loading"
- Clear browser cache
- Check browser console for errors
- Verify `/api/chat` endpoint in dev tools Network tab

## Quick Deploy

Single command from root:

```bash
# Deploy backend
python run_studio.py fly

# Deploy frontend
cd arctic-site && vercel --prod
```

## Status Check

```bash
# Backend
curl https://arcticcodex-studio.fly.dev/api/health

# Frontend
curl https://your-domain.vercel.app/api/health
```

## Cost Estimate

- **Fly.io**: ~$0.25/hour (16GB machine) = ~$180/month
- **Vercel**: Free tier (hobby) or $20/month (Pro)
- **Total**: ~$180-200/month

## Next Steps

1. Deploy backend: `python run_studio.py fly`
2. Get Fly URL: `fly status`
3. Update `.env.local` with Fly URL
4. Deploy frontend: `cd arctic-site && vercel --prod`
5. Test chat at your Vercel URL

---

**Your URLs**:
- Backend (Fly): `https://arcticcodex-studio.fly.dev`
- Frontend (Vercel): `https://your-domain.vercel.app`
- Chat: `https://your-domain.vercel.app/chat`
