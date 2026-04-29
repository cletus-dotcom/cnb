# Home page traceback — PostgreSQL connection closed

Captured from a local Flask run when loading `/` failed with HTTP 500.

## Error

`sqlalchemy.exc.OperationalError` / `psycopg.OperationalError`:

> consuming input failed: server closed the connection unexpectedly  
> This probably means the server terminated abnormally before or while processing the request.

## Location

- View: `app/routes.py` → `home`
- Query: latest published `posts`, ordered by `published_at DESC`, limit 6.

## SQLAlchemy docs (offline copy)

See sibling file `sqlalchemy-error-e3q8.html` (original: https://sqlalche.me/e/20/e3q8).

## Typical fixes (when back online)

- Confirm Postgres / Supabase is running and reachable (`DATABASE_URL` / `.env`).
- Restart the DB or reset idle connections; retry the request.
