# CNB Website (Flask + Supabase Postgres)

Modern, professional, **mobile-first** website for **CNB (Citizens for Nationwide Budget Reform)** with:
- Public pages: Home, About, News list, News detail
- Admin: Login + create/edit/delete News posts
- Database: Postgres (Supabase) via SQLAlchemy
- Hosting: Vercel

## Recommended navbar menu

This repo ships with:
- **About**
- **News**
- **Services**
- **Publications**
- **Contact**
- **Login** (right side)

This is a strong default for professional org sites. If you want it even simpler, remove *Publications* until you have content.

## Local setup (Windows / PowerShell)

Install dependencies:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file:

```powershell
Copy-Item .env.example .env
```

Run DB migrations (first time):

```powershell
$env:FLASK_APP="run.py"
flask db init
flask db migrate -m "init"
flask db upgrade
```

Start the app:

```powershell
py run.py
```

Open `http://localhost:5000`.

## Create the first admin user (local/dev)

1. In `.env`, set:
   - `BOOTSTRAP_ADMIN_TOKEN`
   - `ADMIN_EMAIL`
   - `ADMIN_PASSWORD`
2. Run the app locally
3. Visit:
   - `http://localhost:5000/auth/bootstrap-admin?token=YOUR_TOKEN`
4. Then login at:
   - `http://localhost:5000/auth/login`

## Supabase setup (Postgres)

1. Create a Supabase account
   - Go to Supabase → Sign up → verify email
2. Create a project
   - Project name: `cnb-website`
   - Set a strong database password
   - Choose region closest to your users
3. Get your Postgres connection string
   - Project Settings → Database → Connection string
   - Use the **Session** or **Transaction** string
4. Set `DATABASE_URL` to that connection string
   - Local: in `.env`
   - Vercel: in Environment Variables

Then run:

```powershell
$env:FLASK_APP="run.py"
flask db upgrade
```

## Enable cover image uploads (Supabase Storage)

The admin post form supports **direct cover image uploads** to Supabase Storage.

1. In Supabase: **Storage** → **Create a bucket**
   - Example bucket name: `covers`
   - Set it to **Public** (so the website can display images)
2. In Vercel (and optionally local `.env`), set:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_STORAGE_BUCKET` (example: `covers`)

After that, on **New post / Edit post**, you can choose a file to upload and it will populate `cover_image` automatically.

## Vercel setup + publish (step-by-step)

### A) Create your Vercel account

1. Go to Vercel and click **Sign Up**
2. Choose **Continue with GitHub**
3. Authorize Vercel to access your GitHub account
4. Confirm your email if prompted

### B) Import your GitHub repository

1. In Vercel dashboard, click **Add New…** → **Project**
2. Under **Import Git Repository**, pick your CNB repo
   - If you don’t see it, click **Adjust GitHub App Settings** and allow the repo
3. Vercel will detect a Python project (we provide `vercel.json`)

### C) Add environment variables in Vercel

In the project → **Settings** → **Environment Variables**, add:
- `SECRET_KEY`: generate a long random string
- `DATABASE_URL`: your Supabase Postgres connection string

Optional (only if you want bootstrap on Vercel temporarily):
- `BOOTSTRAP_ADMIN_TOKEN`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Deployments:
- Add them for **Production** (and Preview if you want).

### D) Deploy

1. Click **Deploy**
2. When it finishes, open the production URL

### E) Create admin user (production)

Best practice:
- Create the admin user **locally** (pointing to Supabase DB), then disable bootstrap variables.

If you must do it on Vercel:
1. Set the 3 bootstrap env vars in Vercel
2. Visit `/auth/bootstrap-admin?token=...` once
3. **Remove** `BOOTSTRAP_ADMIN_TOKEN`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` from Vercel

### F) Auto-deploy on GitHub pushes

Vercel automatically redeploys on every push to your repo’s default branch (usually `main`).

## Notes

- Images from `cnb-data/` are copied into `app/static/img/` for deployment.
- The navbar is **fixed** (does not scroll away).

