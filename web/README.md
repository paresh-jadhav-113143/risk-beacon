# Semicolon Web React App

React + TypeScript frontend implementation for the supplier risk MVP screens.

## Screens Implemented

- Supplier review queue
- Supplier risk overview
- Supplier intake profile
- Document checklist and extraction state
- Risk evidence and score components
- Human review and decision controls
- Audit trail and notifications

## Run Locally

```bash
npm install
npm run dev
```

Then open:

```text
http://localhost:5173
```

## Notes

- This is a Vite React app, not a Next.js app.
- The first implementation uses local mock data so the screens can move before backend APIs exist.
- The UI follows the MVP workflow from `implementation-plan.md`.
- Final decisions remain human controlled; AI outputs are presented as advisory evidence.
