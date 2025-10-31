# Deployment Guide - YouTube Clipper v2.0

## Quick Deployment

### Option 1: Using Start Script (Recommended)

```bash
cd youtube-clipper
chmod +x start.sh
./start.sh
```

The script will:
- Check Docker and Docker Compose installation
- Build the Docker image
- Start the application
- Display access URLs

### Option 2: Manual Docker Deployment

```bash
cd youtube-clipper

# Build image
docker-compose build

# Start service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Accessing the Application

### Local Access
```
http://localhost:5000
```

### Network Access (from other devices)
```
http://YOUR_SERVER_IP:5000
```

Find your IP:
- **Linux/Mac:** `hostname -I` or `ifconfig`
- **Windows:** `ipconfig`

## Docker Commands

### Start/Stop
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Stop and remove volumes
docker-compose down -v
```

### Logs and Debugging
```bash
# View logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Access container shell
docker-compose exec youtube-clipper bash

# Check ffmpeg
docker-compose exec youtube-clipper ffmpeg -version

# Check yt-dlp
docker-compose exec youtube-clipper yt-dlp --version
```

### Maintenance
```bash
# Rebuild after changes
docker-compose build --no-cache

# Remove old images
docker image prune

# Check disk usage
docker system df
```

## Data Persistence

Data is stored in `./data` directory on your host machine:

```
youtube-clipper/
└── data/
    ├── VIDEO_ID_1/
    │   ├── VIDEO_ID_1.mp4
    │   ├── original_audio.mp3
    │   ├── VIDEO_ID_1_clip1.mp4
    │   ├── VIDEO_ID_1_clip1.mp3
    │   └── metadata.json
    └── merged/
        ├── merged_video_20251030_152345.mp4
        └── merged_audio_20251030_152345.mp3
```

**To backup your library:**
```bash
# Create backup
tar -czf youtube-clipper-backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf youtube-clipper-backup-20251030.tar.gz
```

## Age-Restricted Videos

To download age-restricted videos:

1. **Get YouTube cookies:**
   - Install browser extension: "Get cookies.txt"
   - Export cookies from YouTube.com
   - Save as `cookies.txt`

2. **Place in project directory:**
   ```bash
   youtube-clipper/
   ├── cookies.txt  # <-- Add here
   ├── docker-compose.yml
   └── ...
   ```

3. **Restart application:**
   ```bash
   docker-compose restart
   ```

The cookies file is automatically mounted (read-only) by Docker.

## Network Configuration

### Firewall (if needed)

**Linux (ufw):**
```bash
sudo ufw allow 5000/tcp
```

**Linux (firewalld):**
```bash
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

**Windows:**
- Windows Defender Firewall → Inbound Rules → New Rule
- Port: 5000
- Protocol: TCP
- Action: Allow

### Change Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Change 8080 to your desired port
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Production Deployment

### Using Reverse Proxy (nginx)

**Install nginx:**
```bash
sudo apt install nginx
```

**Create config:** `/etc/nginx/sites-available/youtube-clipper`
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for large uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

**Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/youtube-clipper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Adding HTTPS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot will automatically:
- Get SSL certificate
- Configure nginx for HTTPS
- Set up auto-renewal

### Adding Authentication

**Option 1: Basic Auth (nginx)**

```bash
# Create password file
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd username

# Add to nginx config
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5000;
    # ... other settings
}
```

**Option 2: Application-level**

Modify `app.py` to add Flask-HTTPAuth or similar.

## Monitoring

### Resource Usage
```bash
# Container stats
docker stats youtube-clipper

# Disk usage
du -sh data/

# Logs size
du -sh /var/lib/docker/containers/
```

### Health Check
```bash
# Check if running
curl http://localhost:5000

# Check API
curl http://localhost:5000/api/videos
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Check Docker daemon
sudo systemctl status docker

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Permission issues
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/

# Or run with correct user (edit docker-compose.yml)
user: "1000:1000"  # Add under youtube-clipper service
```

### Out of disk space
```bash
# Check disk usage
df -h

# Check Docker usage
docker system df

# Clean up
docker system prune -a
rm -rf data/merged/*  # Remove old merged files
```

### Port already in use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

## Upgrade Instructions

### From v1.0 to v2.0

⚠️ **WARNING:** v2.0 is a complete rewrite. Data format is different.

**Option 1: Fresh Start**
```bash
# Backup old data
mv data data-v1-backup

# Deploy v2.0
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Option 2: Manual Migration**

v1.0 used different file structure. If you need old data:
1. Export videos from v1.0
2. Re-download in v2.0
3. Recreate clips manually

### Future Updates

```bash
# Stop application
docker-compose down

# Pull new code
git pull  # if using git

# Rebuild
docker-compose build --no-cache

# Start
docker-compose up -d
```

## Performance Tuning

### For Large Libraries (50+ videos)

**Increase memory limits** in `docker-compose.yml`:
```yaml
services:
  youtube-clipper:
    # ... existing config
    mem_limit: 2g
    cpus: 2
```

### For Slow Network

**Reduce video quality** (modify download command in `app.py`):
```python
'--format', 'best[height<=720]'  # Max 720p instead of best
```

### For Multiple Users

Consider these options:
1. **Increase worker count** (use gunicorn)
2. **Add Redis** for job queue
3. **Use PostgreSQL** instead of JSON
4. See SPECIFICATION.md Section 10.2 for scalability options

## Backup Strategy

### Automated Backups

**Create backup script:** `backup.sh`
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d-%H%M%S)
tar -czf "$BACKUP_DIR/youtube-clipper-$DATE.tar.gz" data/

# Keep only last 7 backups
cd "$BACKUP_DIR"
ls -t youtube-clipper-*.tar.gz | tail -n +8 | xargs rm -f
```

**Add to crontab:**
```bash
crontab -e

# Add: Daily backup at 2 AM
0 2 * * * /path/to/youtube-clipper/backup.sh
```

## Uninstall

### Remove Application
```bash
cd youtube-clipper
docker-compose down -v
cd ..
rm -rf youtube-clipper
```

### Complete Cleanup
```bash
# Remove Docker images
docker rmi youtube-clipper_youtube-clipper

# Remove all unused Docker data
docker system prune -a
```

## Support Checklist

Before asking for help:
- [ ] Check logs: `docker-compose logs -f`
- [ ] Verify Docker/Docker Compose versions
- [ ] Check disk space: `df -h`
- [ ] Try rebuilding: `docker-compose build --no-cache`
- [ ] Check browser console (F12)
- [ ] Review README.md troubleshooting section
- [ ] Test with simple video first

---

**Version:** 2.0  
**Last Updated:** 2025-10-30  
**For:** Docker deployment
