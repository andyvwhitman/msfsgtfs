# Deployment

How to deploy **MSFS-GTFS** to the production Hetzner server. The runtime is unchanged from
the original setup: **gunicorn** serving `backend/wsgi.py` behind an **nginx** reverse proxy,
run as a **systemd** service, with `MSFSGTFS_ENV=production`.

If the server was already provisioned for the original app, you almost certainly only need
the [Updating an existing deployment](#updating-an-existing-deployment) steps. The
[First-time setup](#first-time-setup-from-scratch) section is here for reference / rebuilds.

> Replace the placeholders below with whatever the original install used:
> - `APP_DIR` = `/opt/msfsgtfs` (repo checkout root)
> - `SERVICE` = `msfsgtfs` (systemd unit name)
> - `DOMAIN` = `ferry.example.com`
> - `USER` = the service account that owns the app
>
> Check the existing values with `systemctl cat msfsgtfs` and `nginx -T` before changing anything.

---

## Key facts about this app

- **No database, no runtime secrets, no external API keys.** The GTFS schedule is read from
  `backend/Archive.zip` into memory once at startup.
- **`backend/Archive.zip` is a generated, git-ignored artifact.** It must be (re)built on the
  server from `msfs_gtfs_package/` with `python build_feed.py` — a fresh `git pull` will not
  contain it.
- **`MSFSGTFS_ENV=production` is mandatory.** It disables the dev-only `?now=` time override
  and debug bar. See the [security checklist](#security-checklist).
- **The WSGI entrypoint is `wsgi:app`, and it must be launched from the `backend/` directory**
  (that's where `wsgi.py` and `main.py` live, and the feed path is resolved relative to them).

---

## Updating an existing deployment

The common case — ship the latest code to the already-configured server.

```bash
# On the server, as the service user:
cd /opt/msfsgtfs                      # APP_DIR
git pull

source venv/bin/activate
pip install -r backend/requirements.txt   # only strictly needed if requirements changed

python build_feed.py                  # rebuild backend/Archive.zip from msfs_gtfs_package/

# Restart the service (needs sudo unless the unit is user-scoped)
sudo systemctl restart msfsgtfs
sudo systemctl status msfsgtfs --no-pager
```

Verify it's serving:

```bash
curl -fsS http://127.0.0.1:8000/ | head -n 5    # gunicorn directly
curl -fsSI https://ferry.example.com/           # through nginx + TLS
```

The schedule feed is read **once at startup**, so any change to `msfs_gtfs_package/` only
takes effect after `build_feed.py` **and** a service restart.

### Rollback

```bash
cd /opt/msfsgtfs
git log --oneline -n 5                 # find the previous good commit
git checkout <previous-commit-sha>
python build_feed.py
sudo systemctl restart msfsgtfs
```

(Return to the branch tip with `git checkout main` once a fix is ready.)

---

## First-time setup (from scratch)

Only needed when rebuilding the server. Assumes a fresh Ubuntu/Debian Hetzner box.

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
# geopandas/pyproj/shapely pull in GEOS/PROJ/GDAL — installed via pip wheels here, but if a
# source build is ever needed: sudo apt install -y libgeos-dev libproj-dev gdal-bin
```

### 2. Code + virtualenv

```bash
sudo mkdir -p /opt/msfsgtfs
sudo chown "$USER":"$USER" /opt/msfsgtfs
git clone <your-repo-url> /opt/msfsgtfs
cd /opt/msfsgtfs

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python build_feed.py                   # creates backend/Archive.zip
```

Smoke-test gunicorn before wiring up systemd:

```bash
cd backend
MSFSGTFS_ENV=production ../venv/bin/gunicorn --bind 127.0.0.1:8000 wsgi:app
# Ctrl-C after confirming http://127.0.0.1:8000/ responds
```

### 3. systemd service

Create `/etc/systemd/system/msfsgtfs.service`:

```ini
[Unit]
Description=MSFS-GTFS ferry schedule (gunicorn)
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/opt/msfsgtfs/backend
Environment=MSFSGTFS_ENV=production
ExecStart=/opt/msfsgtfs/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
Restart=on-failure

# Hardening (the app needs no special privileges)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now msfsgtfs
sudo systemctl status msfsgtfs --no-pager
```

Worker count: ~`(2 × CPU cores) + 1` is a reasonable starting point. This app is tiny and
CPU-light; 3 workers is plenty for a single small VPS.

### 4. nginx reverse proxy

Create `/etc/nginx/sites-available/msfsgtfs`:

```nginx
server {
    listen 80;
    server_name ferry.example.com;

    # Serve static assets directly (faster, skips gunicorn)
    location /static/ {
        alias /opt/msfsgtfs/backend/static/;
        expires 7d;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- Security headers (see security checklist below) ---
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options        SAMEORIGIN always;
    add_header Referrer-Policy        strict-origin-when-cross-origin always;
    # Enable after TLS is confirmed working:
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Optional CSP — allows the external scripts this app uses. Tighten if you
    # externalize the inline modal script (see checklist item S2).
    # add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.buymeacoffee.com https://www.vesselfinder.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-src https://www.vesselfinder.com; connect-src 'self'" always;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/msfsgtfs /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5. TLS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ferry.example.com
```

certbot edits the nginx server block to add the `listen 443 ssl` config and a HTTP→HTTPS
redirect, and installs a renewal timer. After confirming HTTPS works, uncomment the
`Strict-Transport-Security` header above and `sudo systemctl reload nginx`.

---

## Security checklist

Pre-deploy review found **no code-level vulnerabilities**; the app has no DB, no auth, no
secrets, and no user-controlled file paths, and Jinja autoescaping is on. The items below are
deployment-time controls and hardening. See the chat/PR notes for full findings.

- [ ] **S0 — `MSFSGTFS_ENV=production` is set** (it's in the systemd unit). Confirm with
      `systemctl show msfsgtfs -p Environment`. Without it, the `?now=` time override and debug
      bar are exposed (low impact, but not for prod).
- [ ] **S1 — Never run the Flask dev server in production.** Use gunicorn only. `flask run` /
      `python main.py` would expose the Werkzeug interactive debugger (remote code execution)
      if `DEV_MODE` were ever on. gunicorn + `wsgi:app` does not start that debugger.
- [ ] **S2 — Third-party scripts (supply chain).** The app loads htmx (`unpkg.com`),
      Buy Me a Coffee (`cdnjs.buymeacoffee.com`), and the VesselFinder map
      (`www.vesselfinder.com`). All are version-or-vendor pinned. Strongest mitigation is the
      CSP above; consider self-hosting/SRI-pinning htmx for full control.
- [ ] **S3 — Security headers at nginx** (included above): `X-Content-Type-Options`,
      `X-Frame-Options`, `Referrer-Policy`, HSTS after TLS, and optionally CSP.
- [ ] **S4 — HTTPS everywhere.** Serve only over TLS (step 5); enable HSTS once confirmed.
- [ ] **S5 — Cookie flags.** The `time_format` / `map_provider` preference cookies are
      cosmetic (no sensitive data) and already use `SameSite=Lax`. Once behind HTTPS, consider
      adding the `Secure` attribute (would require a small code change in the two `/prefs/*`
      routes).
- [ ] **S6 — Open redirect (low).** `/prefs/time-format` and `/prefs/map-provider` redirect to
      `request.referrer`. Cosmetic preference toggles, but for defense-in-depth they could be
      changed to only redirect to local paths.
- [ ] **S7 — Keep dependencies patched.** Periodically `pip list --outdated` and rebuild the
      venv. Current pins are recent (gunicorn 23, Flask 3.1, Werkzeug 3.1.3) and past known
      gunicorn request-smuggling issues.
- [ ] **S8 — Firewall.** Allow only 22/80/443 (e.g. `ufw allow OpenSSH`,
      `ufw allow 'Nginx Full'`, `ufw enable`). gunicorn binds to `127.0.0.1` only, so it is not
      directly reachable from the internet.

---

## Troubleshooting

| Symptom | Check |
| --- | --- |
| 502 Bad Gateway | `systemctl status msfsgtfs`; is gunicorn bound to `127.0.0.1:8000`? `journalctl -u msfsgtfs -n 50` |
| Schedule looks stale / wrong day | Did you run `build_feed.py` **and** restart the service after editing `msfs_gtfs_package/`? |
| `FileNotFoundError: Archive.zip` | `Archive.zip` wasn't built on the server — run `python build_feed.py` from the repo root |
| Debug bar / `?now=` visible in prod | `MSFSGTFS_ENV` is not `production` — fix the systemd `Environment=` line and restart |
| Static files 404 | nginx `alias` path must point at `/opt/msfsgtfs/backend/static/` (trailing slash matters) |
| Import/build errors on `pip install` | geospatial deps (geopandas/pyproj/shapely) — install system GEOS/PROJ/GDAL (step 1 note) |

---

See [Overview → Production](overview.md#production) for the minimal run command, and
[Architecture](architecture.md) for how the pieces fit together.
