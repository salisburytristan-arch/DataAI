# Website Deployment & Ownership Transfer

The site is a Next.js app in `arctic-site/`.

## Run locally

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
npm install
npm run dev
```

## Build

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
npm run build
```

## Vercel

This project was deployed using the Vercel CLI. Local Vercel linkage metadata is stored here:

- `arctic-site/.vercel/project.json`

That file identifies the Vercel project/org IDs:
- `projectId`: `prj_Wlbfhopmb3rqHtSNnBIQKwBisNN5`
- `orgId`: `team_xDD6LgfwQSgYitvhIDjTS3L0`
- `projectName`: `arctic-site`

## Transfer options (buyer)

### Option A (cleanest): Buyer redeploys into their Vercel org

1) Buyer runs:

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
vercel login
vercel
vercel --prod
```

2) Buyer adds their domain in Vercel project settings.

### Option B: Transfer the existing Vercel project

If you want to transfer the Vercel project itself, do it inside Vercel’s UI (team/project transfer).

## Domain transfer notes

Domain transfer depends on your registrar. Typical buyer steps:
- Initiate domain transfer (or change account owner)
- Update DNS to point to the buyer’s Vercel project
- Confirm SSL provisioning in Vercel

## Contact email

The site uses a mailto contact link:
- `ArctiCasters@gmail.com`

Update in `arctic-site/app/page.tsx` if needed.
