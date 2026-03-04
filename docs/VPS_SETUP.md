# Open Booth — VPS Setup Guide

DigitalOcean · Ubuntu 24 · $6/month
Everything — recorder, monitor, and chunk server — runs on one droplet.

---

## Architecture

```
Your droplet (143.198.x.x)
├── Nginx (port 80)
│   ├── /                 → serves recorder.html + monitor.html
│   ├── /upload           → proxies to chunk server
│   ├── /register         → proxies to chunk server
│   ├── /session-command  → proxies to chunk server
│   ├── /session-commands → proxies to chunk server
│   ├── /session-state    → proxies to chunk server
│   └── /health           → proxies to chunk server
└── Chunk server (port 8080, internal only)
    └── /opt/openbooth/chunks/
```

Open `http://YOUR_IP/recorder.html` — that's it.

---

## PART 0 — Get the code

You need a copy of the Open Booth files on your Mac before you can set up the server.

### Step 1: Download or clone the repo

Pick **one** of these two options:

**Option A — Git clone (recommended if you have git installed)**

```bash
git clone https://github.com/tklrstudio/Open-Booth.git
```

This creates an `Open-Booth/` folder in your current directory.

**Option B — Download ZIP (no git required)**

1. Go to https://github.com/tklrstudio/Open-Booth
2. Click the green **Code** button → **Download ZIP**
3. Unzip the file — this creates a folder called `Open-Booth-main/`

### Step 2: Set your project path

The rest of this guide uses `$OB` to refer to your Open Booth folder. Set it now so every command works regardless of how you got the files.

**If you used git clone:**
```bash
OB=~/Open-Booth
```

**If you downloaded the ZIP:**
```bash
OB=~/Downloads/Open-Booth-main
```

Adjust the path if you cloned or unzipped somewhere else. You can check it worked:
```bash
ls $OB/scripts/server.py $OB/client/recorder.html
```

Both files should exist. If you get "No such file", double-check the path.

> **Note:** `$OB` is a shell variable — it only lasts for your current terminal session. If you close the terminal and come back later, run the `OB=...` line again before using any `$OB` commands.

---

## PART 1 — Create your server

### Step 3: Create a DigitalOcean account

Go to https://digitalocean.com and sign up.
You'll need a credit card. Cost is $6/month.

---

### Step 4: Create a Droplet

1. Click **Create → Droplets**
2. Region: **Choose the region closest to you** (e.g. Sydney, San Francisco, London, Frankfurt, Singapore — pick whichever has the lowest latency to your location)
3. Image: **Ubuntu 24.04 (LTS) x64**
4. Size: **Basic → Regular → $6/month** (1GB RAM, 1 CPU, 25GB disk)
5. Authentication: **Password** — set a strong one and save it somewhere
6. Hostname: `openbooth`
7. Click **Create Droplet**

Wait ~60 seconds. Your droplet appears with an IP like `143.198.xxx.xxx`.
**Write down that IP address.**

---

## PART 2 — Connect to your server

### Step 5: Open Terminal on your Mac

`Cmd + Space` → type `Terminal` → Enter.

### Step 6: SSH in

```bash
ssh root@YOUR_IP
```

First connection shows a fingerprint warning — type `yes` and Enter.
Enter your password when prompted.

Your prompt becomes:
```
root@openbooth:~#
```

You're now on the remote machine. Same commands as your Mac terminal, different computer.

---

## PART 3 — Install software

Run these one at a time. Wait for each to finish.

### Step 7: Update the system

```bash
apt update && apt upgrade -y
```

Takes a minute or two.

### Step 8: Install Nginx

```bash
apt install nginx -y
```

### Step 9: Verify Nginx is running

```bash
systemctl status nginx
```

Should show `Active: active (running)`.

Test from your Mac (open a new terminal tab, keep the server tab open):
```bash
curl http://YOUR_IP
```

You should get back an HTML page (Nginx's default welcome page). If so, Nginx is working.

---

## PART 4 — Upload your files

Open a **new Terminal tab on your Mac** for this part. Make sure `$OB` is set (see Step 2).

### Step 10: Create the app directory on the server

Back in your server terminal tab:
```bash
mkdir -p /opt/openbooth/chunks
mkdir -p /var/www/openbooth
```

### Step 11: Upload all files from your Mac

In your Mac terminal tab:
```bash
# Upload the chunk server
scp $OB/scripts/server.py root@YOUR_IP:/opt/openbooth/server.py

# Upload the HTML files
scp $OB/client/recorder.html root@YOUR_IP:/var/www/openbooth/recorder.html
scp $OB/client/monitor.html  root@YOUR_IP:/var/www/openbooth/monitor.html
```

Each will ask for your password.

---

## PART 5 — Configure Nginx

### Step 12: Create the Nginx config

In your server terminal, run this whole block — copy and paste all of it:

```bash
cat > /etc/nginx/sites-available/openbooth << 'EOF'
server {
    listen 80;
    server_name _;

    # Serve HTML files
    root /var/www/openbooth;
    index recorder.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Proxy API calls to chunk server
    location /upload {
        proxy_pass         http://localhost:8080;
        proxy_set_header   Host $host;
        client_max_body_size 200M;
        proxy_read_timeout 300s;
    }

    location /register {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }

    location /session-command {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }

    location /session-commands {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }

    location /session-state {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }

    location /health {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }

    location /sessions {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
    }
}
EOF
```

### Step 13: Enable the config

```bash
# Enable our site
ln -s /etc/nginx/sites-available/openbooth /etc/nginx/sites-enabled/openbooth

# Disable the default Nginx page
rm /etc/nginx/sites-enabled/default

# Test the config is valid
nginx -t
```

You should see:
```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 14: Reload Nginx

```bash
systemctl reload nginx
```

---

## PART 6 — Run the chunk server

### Step 15: Create a systemd service

Paste this whole block:

```bash
cat > /etc/systemd/system/openbooth.service << 'EOF'
[Unit]
Description=Open Booth Chunk Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/openbooth
ExecStart=/usr/bin/python3 /opt/openbooth/server.py --port 8080 --chunks-dir /opt/openbooth/chunks
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### Step 16: Start and enable it

```bash
systemctl daemon-reload
systemctl enable openbooth
systemctl start openbooth
```

### Step 17: Check it's running

```bash
systemctl status openbooth
```

Should show `Active: active (running)`.

---

## PART 7 — Open the firewall

### Step 18: Allow web traffic

In the DigitalOcean web dashboard:

1. Click your droplet → **Networking** tab → **Firewalls**
2. **Create Firewall**, name it `openbooth`
3. Under **Inbound Rules**, add:

| Type | Protocol | Port | Sources |
|------|----------|------|---------|
| HTTP | TCP | 80 | All IPv4, All IPv6 |
| Custom | TCP | 22 | All IPv4, All IPv6 |

Port 8080 does NOT need to be open — Nginx handles it internally.

4. Click **Create Firewall** → assign to your droplet

---

## PART 8 — Configure and upload

### Step 19: Create your config file

On your Mac, copy the example config:

```bash
cp $OB/client/config.example.js $OB/client/config.js
```

Open `$OB/client/config.js` in any text editor and set your server's IP:

```javascript
const OB_CONFIG = {
  UPLOAD_ENDPOINT:   'http://YOUR_IP/upload',
  SESSION_STATE_URL: 'http://YOUR_IP/session-state',
};
```

### Step 20: Upload the config file

```bash
scp $OB/client/config.js root@YOUR_IP:/var/www/openbooth/config.js
```

---

## PART 9 — Test everything

### Step 21: Full smoke test

From your Mac browser, open:
```
http://YOUR_IP/recorder.html
```

You should see the Open Booth recorder page. Enter a name, allow camera/mic, hit Start Recording, record for 30 seconds, hit Stop.

Then check the server received the chunks:
```bash
ssh root@YOUR_IP
ls /opt/openbooth/chunks/
```

You should see a folder named with your session ID containing chunk files.

Open the monitor:
```
http://YOUR_IP/monitor.html?session=OB-YYYYMMDD-XXXX
```

(Replace with the session ID from your recorder URL.)

---

## Session Workflow

### Host and guest roles

One participant can act as the **host** by adding `?role=host` to their recorder URL. The host gets coordination controls; everyone else is a guest.

**Host URL:**
```
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX&role=host
```

**Guest URL (same session, no role):**
```
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX
```

### What the host can do

- **Start All / Stop All** — starts or stops recording for all participants simultaneously
- **Chapter markers** — drops a named marker at the current timestamp for post-production editing

### What guests see

- A "Controlled by [host]" status line appears
- Manual start/stop buttons are dimmed but remain functional as a manual override
- Recording starts and stops automatically when the host presses Start All / Stop All

### Fallback

If the server becomes unreachable (3 consecutive poll failures), guests automatically exit controlled mode and regain full manual control. Recording in progress is not interrupted.

Roles are optional — if nobody uses `?role=host`, Open Booth works exactly as before.

---

## UI Skins

Add `?skin=name` to the recorder URL to change the visual theme. The default terminal theme is used when no skin is specified.

| Skin | Description |
|------|-------------|
| `studio-warm` | Charcoal + amber/gold. Warm recording booth feel. |
| `clean-light` | White, minimal, indigo accent. Notion-like. |
| `soft-dark` | Muted purple, rounded corners. Discord/Spotify. |
| `broadcast` | Deep navy + red/white. Bold TV control room. |
| `analog` | Cream, rust, serif type. Vintage audio gear. |
| `glass` | Frosted panels, violet accent. Apple-esque. |
| `campfire` | Dark charcoal + orange/ember. Cozy. |
| `newsroom` | Light, sharp black borders, red accent. Editorial. |

Example:
```
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX&skin=glass
```

Skins can be combined with host roles:
```
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX&role=host&skin=campfire
```

---

## After each episode

### Download and assemble

```bash
# On your Mac — download the session chunks
scp -r root@YOUR_IP:/opt/openbooth/chunks/OB-20260306-A3BX ~/Podcasts/chunks/

# Assemble
python3 $OB/scripts/assemble.py OB-20260306-A3BX --chunks-dir ~/Podcasts/chunks/OB-20260306-A3BX
```

### Clean up the server

```bash
ssh root@YOUR_IP
rm -rf /opt/openbooth/chunks/OB-20260306-A3BX
```

Don't leave chunks on the server indefinitely — 25GB fills faster than you'd think with video.

---

## Useful commands

```bash
# Check chunk server is running
systemctl status openbooth

# Restart chunk server
systemctl restart openbooth

# Watch chunk server logs live
journalctl -u openbooth -f

# Check Nginx is running
systemctl status nginx

# Reload Nginx after config changes
systemctl reload nginx

# Check disk space
df -h

# List sessions on server
ls /opt/openbooth/chunks/

# Health check
curl http://YOUR_IP/health
```

---

## Troubleshooting

**Browser can't reach http://YOUR_IP**
- Check firewall rule — port 80 must be open
- Run `systemctl status nginx` on server

**Recorder loads but chunks don't upload**
- Check UPLOAD_ENDPOINT in config.js has your actual IP
- Check chunk server: `systemctl status openbooth`
- Watch live logs during a test: `journalctl -u openbooth -f`
- Check browser console (F12) for errors

**`nginx -t` shows an error**
- Usually a typo in the config
- Run `cat /etc/nginx/sites-available/openbooth` to inspect it
- Re-paste the config block from Step 12

**"Permission denied" on SSH**
- Make sure you're typing `root@YOUR_IP` with the right IP
- Try the DigitalOcean web console (droplet → Console tab) as a backup

---

## Adding HTTPS later (optional)

When you want a proper `https://` URL:

1. Buy a domain (~$15/year at Namecheap or Cloudflare Registrar)
2. Point it at your droplet IP (an A record in DNS)
3. Install Certbot:
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d yourdomain.com
   ```
4. Certbot updates your Nginx config automatically and renews certificates
5. Update UPLOAD_ENDPOINT and SESSION_STATE_URL in config.js to use `https://`

---

## Monthly cost

| Item | Cost |
|------|------|
| DigitalOcean droplet (1GB) | $6/month |
| Everything else | Free |
| **Total** | **$6/month** |
