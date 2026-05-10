# Batcave Portfolio (Next.js + Django)

Batman-inspired dark portfolio frontend with a Django backend, designed to deploy on free Vercel.

## Stack

- Frontend: Next.js App Router + Tailwind CSS
- Backend: Django (WSGI entry in `api/index.py`)
- Hosting: Vercel (single project)

## Local development

### 1) Frontend

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 2) Backend (local run)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Try:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/projects`

## Deploy to Vercel (free)

1. Push this repo to GitHub.
2. Import the repo in Vercel.
3. Keep framework preset as Next.js.
4. Deploy.

`vercel.json` is already configured to route `/api/*` to Django via `api/index.py`.

## Customize content

- UI content cards: `src/app/page.tsx`
- Theme and gradients: `src/app/globals.css`
- API responses: `api/index.py`
