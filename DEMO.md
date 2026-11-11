# Demo with a public link (Cloudflare Tunnel)

Share the app running on your laptop (or the college Workstation) through a free, temporary HTTPS link. Judges open it on any phone or laptop. HTTPS means the camera, GPS and **Add to Home screen** all work.

Last link used: `https://depend-relatives-musician-once.trycloudflare.com`
(it changes every time the tunnel restarts, so make a new QR code on demo day)

## 1. Install cloudflared (one time)

- **Windows** (PowerShell): `winget install --id Cloudflare.cloudflared`
- **Mac**: `brew install cloudflared`
- **Linux**: download `cloudflared-linux-amd64` from https://github.com/cloudflare/cloudflared/releases

No Cloudflare account is needed.

## 2. Build and start the app (terminal 1)

Build the frontend once:

```bash
cd frontend
npm install
npm run build
```

Start the server (it also serves the built app):

```bash
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check that http://localhost:8000 opens on the laptop.

## 3. Start the tunnel (terminal 2)

```bash
cloudflared tunnel --url http://localhost:8000
```

It prints a link like `https://random-words-1234.trycloudflare.com`. Anyone can open it.

## 4. Share it

Make a QR code from the link (any QR code generator) and show it on your demo screen or slide. Judges scan it and use the demo login buttons.

## 5. Check before judging (2 minutes)

1. **Laptop:** open the link. The login page appears.
2. **Phone on mobile data** (not your Wi-Fi): open the same link. This proves outside users can reach it.
3. **Full flow on the phone:**
   - **Resident:** take a photo, tap **Use my location**, send. Allow camera and location when asked.
   - **Officer** (on the laptop): the new pin appears. Assign it to **Murugan**.
   - **Field worker** (`worker1`): add an after photo, mark it cleaned.
   - **Officer:** **Verify and close**.
4. **Install:** phone browser menu → **Add to Home screen**. It opens like an app.

## If something fails

| You see | Fix |
|---|---|
| Blank page or "Not Found" | `npm run build` was not run in `frontend`. Run it, then restart `uvicorn`. |
| "Cannot reach the server" | The `uvicorn` terminal stopped. Start it again. |
| Error 1033 / 502 | The tunnel cannot reach the app. Check that http://localhost:8000 works on the laptop. |
| Location not working | Allow location for the site in the phone browser settings, or tap the map instead. |
| Map is grey | The phone has no internet for map tiles. Pins still work. |

## Keep in mind

- The link stops when the laptop sleeps or either terminal closes. Keep the laptop plugged in and awake.
- Cloudflare gives no uptime guarantee for these free links. Keep backups: the app on `localhost:8000` on your screen, and a 2–3 minute demo video.
- The college Workstation is a steadier place to run it than a laptop.
