# Ubuntu Server Deployment Guide (AWS EC2)

Date: 2026-02-27  
Scope: Deploy `data_migration` full stack (FastAPI + Next.js + pipeline) on AWS Ubuntu.

## 1. Target runtime and ports

1. Backend API: `9134`
2. Frontend UI: `9133`
3. Auth entrypoint: `/login`
3. Recommended public exposure: `443` via Nginx reverse proxy

## 2. AWS prerequisites

1. EC2 Ubuntu 22.04 or 24.04 instance.
2. Security group rules:
- inbound `22` (SSH)
- inbound `9133` and `9134` for direct testing (optional)
- inbound `80/443` if using Nginx (recommended)
3. Sufficient disk and memory for npm build and pipeline artifacts.

## 3. Install system dependencies

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm nginx
```

Optional (version-managed Node):

```bash
sudo npm install -g n
sudo n 20
node -v
npm -v
```

## 4. Clone the repository

```bash
cd /opt
sudo git clone https://github.com/zhongli1990/nhs-dm-tool.git
sudo chown -R $USER:$USER /opt/nhs-dm-tool
cd /opt/nhs-dm-tool/data_migration
```

## 5. Backend setup (FastAPI)

```bash
cd /opt/nhs-dm-tool/data_migration/product/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create backend env file:

```bash
cat > /opt/nhs-dm-tool/data_migration/product/backend/.env << 'EOF'
DM_ENV=prod
DM_LOG_LEVEL=INFO
DM_ALLOW_ORIGINS=*
DM_API_HOST=0.0.0.0
DM_API_PORT=9134
EOF
```

## 6. Frontend setup (Next.js)

```bash
cd /opt/nhs-dm-tool/data_migration/product/frontend
npm install
```

Create frontend env file:

```bash
cat > /opt/nhs-dm-tool/data_migration/product/frontend/.env.local << 'EOF'
NEXT_PUBLIC_DM_API_BASE=http://127.0.0.1:9134
EOF
```

Build frontend:

```bash
npm run build
```

## 7. Run pipeline lifecycle once (artifact bootstrap)

```bash
cd /opt/nhs-dm-tool/data_migration
python3 pipeline/run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

## 8. Create systemd services

## 8.1 Backend service

```bash
sudo tee /etc/systemd/system/nhs-dm-backend.service > /dev/null << 'EOF'
[Unit]
Description=NHS DM Backend (FastAPI)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/nhs-dm-tool/data_migration/product/backend
EnvironmentFile=/opt/nhs-dm-tool/data_migration/product/backend/.env
ExecStart=/opt/nhs-dm-tool/data_migration/product/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9134
Restart=always
RestartSec=3
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF
```

## 8.2 Frontend service

```bash
sudo tee /etc/systemd/system/nhs-dm-frontend.service > /dev/null << 'EOF'
[Unit]
Description=NHS DM Frontend (Next.js)
After=network.target nhs-dm-backend.service

[Service]
Type=simple
WorkingDirectory=/opt/nhs-dm-tool/data_migration/product/frontend
Environment=PORT=9133
ExecStart=/usr/bin/npm run start -- -p 9133
Restart=always
RestartSec=3
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nhs-dm-backend nhs-dm-frontend
sudo systemctl start nhs-dm-backend nhs-dm-frontend
```

Check status:

```bash
sudo systemctl status nhs-dm-backend --no-pager
sudo systemctl status nhs-dm-frontend --no-pager
```

## 9. Nginx reverse proxy (recommended)

```bash
sudo tee /etc/nginx/sites-available/nhs-dm > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:9134/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:9133;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/nhs-dm /etc/nginx/sites-enabled/nhs-dm
sudo nginx -t
sudo systemctl restart nginx
```

## 10. Verification checklist

1. Backend health:

```bash
curl -s http://127.0.0.1:9134/health
```

2. Frontend health:

```bash
curl -I http://127.0.0.1:9133/login
```

3. Connector types API:

```bash
curl -s http://127.0.0.1:9134/api/connectors/types
```

4. Open UI:
- direct: `http://<EC2_PUBLIC_IP>:9133`
- via nginx: `http://<EC2_PUBLIC_IP>`

## 11. Gap analysis vs current Windows test baseline

Linux is fully viable now. Remaining non-OS-specific gaps are:
1. ODBC/JDBC connectors are experimental and not production-hardened.
2. Security controls still need production uplift:
- strict CORS (remove wildcard)
- authentication and RBAC
- secret vault integration
3. Lifecycle job execution still uses subprocess model (move to async queue for scale).
4. Observability should be extended for production:
- centralized logs
- alerting
- run audit retention policy

## 12. User management (Docker Compose)

When the platform is deployed via Docker Compose, use these commands to manage user accounts directly in the database.

### 12.1 List all users

```bash
docker exec dmm-postgres psql -U dmm_app -d dmm \
  -c "SELECT email, display_name, status, is_super_admin FROM users ORDER BY email;"
```

### 12.2 Reset all user passwords

Passwords are hashed with PBKDF2-SHA256. Generate the hash using the backend's own security module, then update the database.

```bash
docker exec dmm-backend python -c "
import sys, os
sys.path.insert(0, '/app/services/backend')
from app.security import hash_password
import psycopg2
new_hash = hash_password('NEW_PASSWORD_HERE')
conn = psycopg2.connect(os.environ.get('DM_DATABASE_URL', 'postgresql://dmm_app:change_me_postgres_password@postgres:5432/dmm'))
cur = conn.cursor()
cur.execute('UPDATE users SET password_hash = %s', (new_hash,))
conn.commit()
print(f'Updated {cur.rowcount} users')
cur.close()
conn.close()
"
```

Replace `NEW_PASSWORD_HERE` with the desired password.

The reported row count is the number of application login accounts currently present in the `users` table. In a freshly bootstrapped environment this may be only the two default users.

### 12.3 Reset a single user's password

```bash
docker exec dmm-backend python -c "
import sys, os
sys.path.insert(0, '/app/services/backend')
from app.security import hash_password
import psycopg2
new_hash = hash_password('NEW_PASSWORD_HERE')
conn = psycopg2.connect(os.environ.get('DM_DATABASE_URL', 'postgresql://dmm_app:change_me_postgres_password@postgres:5432/dmm'))
cur = conn.cursor()
cur.execute('UPDATE users SET password_hash = %s WHERE email = %s', (new_hash, 'TARGET_EMAIL'))
conn.commit()
print(f'Updated {cur.rowcount} user(s)')
cur.close()
conn.close()
"
```

Replace `NEW_PASSWORD_HERE` and `TARGET_EMAIL` with the desired values.

### 12.4 Invalidate all sessions and unlock accounts

Force all users to re-login with their new password and restore any locked accounts to `ACTIVE`:

```bash
docker exec dmm-postgres psql -U dmm_app -d dmm \
  -c "UPDATE users SET status = 'ACTIVE', session_revoked_at_utc = NOW()::text, failed_login_count = 0, locked_until_utc = '' WHERE TRUE;"
```

The login flow denies access to any user whose `status` is not `ACTIVE`, so clearing `locked_until_utc` alone does not unlock a user that is already marked `LOCKED`.

### 12.5 Verify login works

```bash
curl -s -X POST http://localhost:9134/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "TARGET_EMAIL", "password": "NEW_PASSWORD_HERE"}' | python3 -m json.tool
```

A successful response returns an `access_token` and `user` object.

## 13. Operations commands

Restart services:

```bash
sudo systemctl restart nhs-dm-backend nhs-dm-frontend nginx
```

View live logs:

```bash
journalctl -u nhs-dm-backend -f
journalctl -u nhs-dm-frontend -f
```

Stop services:

```bash
sudo systemctl stop nhs-dm-backend nhs-dm-frontend
```

Docker Compose restart (when deployed via containers):

```bash
cd /path/to/nhs-dm-tool
docker compose restart
```

Docker Compose live logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```
