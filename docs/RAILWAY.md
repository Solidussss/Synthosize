# Hosted studio on Railway

This edition is a **single-owner private workspace**, not a public multi-user SaaS. Anyone with the studio password shares the same media and scenes. Uploads leave the browser and are stored on the Railway volume.

The `Dockerfile` installs Python, FFmpeg, Flask and Waitress. The entrypoint gives the app's dedicated user ownership of the volume root and drops privileges. The app listens on `0.0.0.0:$PORT`; Railway terminates HTTPS. Only `/health` and the sign-in page are public. Sessions use signed, HttpOnly, Secure, SameSite=Strict cookies. Authenticated state-changing requests require a session CSRF token; login has its own CSRF token and a short failed-attempt rate limit.

Required service variables:

| Variable | Value |
|---|---|
| `PORT` | `8080` |
| `STUDIO_DATA_DIR` | `/data` |
| `STUDIO_PUBLIC_ORIGIN` | Exact HTTPS origin of the deployed studio |
| `STUDIO_SESSION_SECRET` | Random secret with at least 32 characters; never commit |
| `STUDIO_PASSWORD_HASH` | Werkzeug password hash; never commit the plaintext password |

Generate a password hash interactively without putting the password in shell history:

```sh
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Studio password: ')))"
```

Attach a persistent volume at `/data`. Use one replica and one service process because scenes, caches and export jobs belong to that process/volume. Pushes to the connected GitHub branch should deploy the Dockerfile. The healthcheck is `/health`.

Imports are capped at 100 MB on the hosted edition; decoded visual caches and portable backups can require much more disk. Stop importing when the free-space guard is reached. Back up scenes regularly. Export jobs run in a background thread; redeploying interrupts an in-progress export, but completed exports and saved scenes remain on the volume. There is no automatic cache/export cleanup yet.

Browser preview now crosses the internet, so its 24 FPS target is not a latency guarantee. MP4 export still evaluates exact frame times. A later client-side/GPU preview will be needed for a polished hosted editor.

## Local hosted-mode testing

```sh
python -m pip install -r requirements-hosted.txt
python -m unittest discover -s tests -v
```

The automated Flask tests use an isolated temporary store, a test-only password and non-Secure cookies for local HTTP only. Production cookies always default to Secure. The desktop-only entrypoint remains `python -m engine.server --open`.
