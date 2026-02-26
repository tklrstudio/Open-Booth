# Fresh Rubber — VPS Setup Guide

DigitalOcean Sydney · Ubuntu 24 · $6/month
Everything — recorder, monitor, and chunk server — runs on one droplet.

---

## Architecture

```
Your droplet (143.198.x.x)
├── Nginx (port 80)
│   ├── /              → serves recorder.html + monitor.html
│   └── /upload        → proxies to chunk server
│   └── /session-state → proxies to chunk server
│   └── /health        → proxies to chunk server
└── Chunk server (port 8080, internal only)
    └── /opt/freshrubber/chunks/
```

Gav opens `http://YOUR_IP/recorder.html` — that's it.

---

## PART 1 — Create your server

### Step 1: Create a DigitalOcean account

Go to https://digitalocean.com and sign up.
You'll need a credit card. Cost is $6/month.

---

### Step 2: Create a Droplet

1. Click **Create → Droplets**
2. Region: **Sydney**
3. Image: **Ubuntu 24.04 (LTS) x64**
4. Size: **Basic → Regular → $6/month** (1GB RAM, 1 CPU, 25GB disk)
5. Authentication: **Password** — set a strong one and save it somewhere
6. Hostname: `freshrubber`
7. Click **Create Droplet**

Wait ~60 seconds. Your droplet appears with an IP like `143.198.xxx.xxx`.
**Write down that IP address.**

---

## PART 2 — Connect to your server

### Step 3: Open Terminal on your Mac

`Cmd + Space` → type `Terminal` → Enter.

### Step 4: SSH in

```bash
ssh root@YOUR_IP
```

First connection shows a fingerprint warning — type `yes` and Enter.
Enter your password when prompted.

Your prompt becomes:
```
root@freshrubber:~#
```

You're now on the remote machine. Same commands as your Mac terminal, different computer.

---

## PART 3 — Install software

Run these one at a time. Wait for each to finish.

### Step 5: Update the system

```bash
apt update && apt upgrade -y
```

Takes a minute or two.

### Step 6: Install Nginx

```bash
apt install nginx -y
```

### Step 7: Verify Nginx is running

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

Open a **new Terminal tab on your Mac** for this part. Replace paths with wherever you saved the files.

### Step 8: Create the app directory on the server

Back in your server terminal tab:
```bash
mkdir -p /opt/freshrubber/chunks
mkdir -p /var/www/freshrubber
```

### Step 9: Upload all files from your Mac

In your Mac terminal tab:
```bash
# Upload the chunk server
scp ~/Downloads/server.py root@YOUR_IP:/opt/freshrubber/server.py

# Upload the HTML files
scp ~/Downloads/recorder.html root@YOUR_IP:/var/www/freshrubber/recorder.html
scp ~/Downloads/monitor.html  root@YOUR_IP:/var/www/freshrubber/monitor.html
```

Each will ask for your password. You can also do all three at once:
```bash
scp ~/Downloads/server.py ~/Downloads/recorder.html ~/Downloads/monitor.html root@YOUR_IP:/tmp/
```

Then in your server terminal tab, move them:
```bash
mv /tmp/server.py   /opt/freshrubber/server.py
mv /tmp/recorder.html /var/www/freshrubber/recorder.html
mv /tmp/monitor.html  /var/www/freshrubber/monitor.html
```

---

## PART 5 — Configure Nginx

### Step 10: Create the Nginx config

In your server terminal, run this whole block — copy and paste all of it:

```bash
cat > /etc/nginx/sites-available/freshrubber << 'EOF'
server {
    listen 80;
    server_name _;

    # Serve HTML files
    root /var/www/freshrubber;
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

### Step 11: Enable the config

```bash
# Enable our site
ln -s /etc/nginx/sites-available/freshrubber /etc/nginx/sites-enabled/freshrubber

# Disable the default Nginx page
rm /etc/nginx/sites-enabled/default

# Test the config is valid
nginx -t
```

You should see:
```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 12: Reload Nginx

```bash
systemctl reload nginx
```

---

## PART 6 — Run the chunk server

### Step 13: Create a systemd service

Paste this whole block:

```bash
cat > /etc/systemd/system/freshrubber.service << 'EOF'
[Unit]
Description=Fresh Rubber Chunk Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/freshrubber
ExecStart=/usr/bin/python3 /opt/freshrubber/server.py --port 8080 --chunks-dir /opt/freshrubber/chunks
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### Step 14: Start and enable it

```bash
systemctl daemon-reload
systemctl enable freshrubber
systemctl start freshrubber
```

### Step 15: Check it's running

```bash
systemctl status freshrubber
```

Should show `Active: active (running)`.

---

## PART 7 — Open the firewall

### Step 16: Allow web traffic

In the DigitalOcean web dashboard:

1. Click your droplet → **Networking** tab → **Firewalls**
2. **Create Firewall**, name it `freshrubber`
3. Under **Inbound Rules**, add:

| Type | Protocol | Port | Sources |
|------|----------|------|---------|
| HTTP | TCP | 80 | All IPv4, All IPv6 |
| Custom | TCP | 22 | All IPv4, All IPv6 |

Port 8080 does NOT need to be open — Nginx handles it internally.

4. Click **Create Firewall** → assign to your droplet

---

## PART 8 — Update the HTML files

The recorder and monitor files still have `null` for the endpoints.
You need to update them with your actual IP, then re-upload.

### Step 17: Edit recorder.html on your Mac

Open `recorder.html` in any text editor. Find these lines near the top of the script:

```javascript
const UPLOAD_ENDPOINT  = null;
```

Change to:

```javascript
const UPLOAD_ENDPOINT  = 'http://YOUR_IP/upload';
```

### Step 18: Edit monitor.html on your Mac

Find:
```javascript
const SESSION_STATE_URL = null;
```

Change to:
```javascript
const SESSION_STATE_URL = 'http://YOUR_IP/session-state';
```

### Step 19: Re-upload the updated files

```bash
scp ~/Downloads/recorder.html root@YOUR_IP:/var/www/freshrubber/recorder.html
scp ~/Downloads/monitor.html  root@YOUR_IP:/var/www/freshrubber/monitor.html
```

---

## PART 9 — Test everything

### Step 20: Full smoke test

From your Mac browser, open:
```
http://YOUR_IP/recorder.html
```

You should see the Fresh Rubber recorder page. Enter a name, allow camera/mic, hit Start Recording, record for 30 seconds, hit Stop.

Then check the server received the chunks:
```bash
ssh root@YOUR_IP
ls /opt/freshrubber/chunks/
```

You should see a folder named with your session ID containing chunk files.

Open the monitor:
```
http://YOUR_IP/monitor.html?session=FR-YYYYMMDD-XXXX
```

(Replace with the session ID from your recorder URL.)

---

## After each episode

### Download and assemble

```bash
# On your Mac — download the session chunks
scp -r root@YOUR_IP:/opt/freshrubber/chunks/FR-20260306-A3BX ~/Podcasts/chunks/

# Assemble
python3 assemble.py FR-20260306-A3BX --chunks-dir ~/Podcasts/chunks/FR-20260306-A3BX
```

### Clean up the server

```bash
ssh root@YOUR_IP
rm -rf /opt/freshrubber/chunks/FR-20260306-A3BX
```

Don't leave chunks on the server indefinitely — 25GB fills faster than you'd think with video.

---

## Useful commands

```bash
# Check chunk server is running
systemctl status freshrubber

# Restart chunk server
systemctl restart freshrubber

# Watch chunk server logs live
journalctl -u freshrubber -f

# Check Nginx is running
systemctl status nginx

# Reload Nginx after config changes
systemctl reload nginx

# Check disk space
df -h

# List sessions on server
ls /opt/freshrubber/chunks/

# Health check
curl http://YOUR_IP/health
```

---

## Troubleshooting

**Browser can't reach http://YOUR_IP**
- Check firewall rule — port 80 must be open
- Run `systemctl status nginx` on server

**Recorder loads but chunks don't upload**
- Check UPLOAD_ENDPOINT in recorder.html has your actual IP
- Check chunk server: `systemctl status freshrubber`
- Watch live logs during a test: `journalctl -u freshrubber -f`
- Check browser console (F12) for errors

**`nginx -t` shows an error**
- Usually a typo in the config
- Run `cat /etc/nginx/sites-available/freshrubber` to inspect it
- Re-paste the config block from Step 10

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
5. Update UPLOAD_ENDPOINT and SESSION_STATE_URL to use `https://`

The whole HTTPS upgrade takes about 10 minutes once you have a domain.

---

## Monthly cost

| Item | Cost |
|------|------|
| DigitalOcean droplet (Sydney, 1GB) | $6/month |
| Everything else | Free |
| **Total** | **$6/month** |
