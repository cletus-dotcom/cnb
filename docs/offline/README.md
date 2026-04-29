# Offline documentation and vendor assets

This folder holds copies of external URLs referenced in development (including the SQLAlchemy error doc link from Flask tracebacks) so you can read them without internet.

## Contents

| Path | Description |
|------|-------------|
| `sqlalchemy-error-e3q8.html` | Cached HTML for https://sqlalche.me/e/20/e3q8 (SQLAlchemy `OperationalError` background). Open in a browser. |
| `vendor/bootstrap-5.3.3.min.css` | Bootstrap 5.3.3 stylesheet from jsDelivr. |
| `vendor/bootstrap-5.3.3.bundle.min.js` | Bootstrap 5.3.3 bundle from jsDelivr. |
| `vendor/google-fonts-montserrat-playfair.css` | Original Google Fonts CSS response (remote font URLs). |
| `vendor/google-fonts-local.css` | **Offline-safe** `@font-face` rules pointing at files under `vendor/fonts/`. |
| `vendor/fonts/*.ttf` | Montserrat and Playfair Display font files used by the site theme. |
| `traceback-home-operational-error.md` | Notes from the local traceback when Postgres closed the connection. |
| `external-urls-manifest.json` | URLs pulled from templates / common deps for reference. |

## Using offline Bootstrap + fonts in the app

In `app/templates/layout.html`, you can point to Flask static files instead of CDNs, for example:

- Serve these files from `app/static/vendor/` (copy from `docs/offline/vendor/` as needed), then use `url_for('static', filename='vendor/...')`.

Embedded third-party pages (Facebook plugin, YouTube iframe, Google Maps embed) still require network unless you replace them with static placeholders.
