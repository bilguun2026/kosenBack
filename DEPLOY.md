# MUST KOOSEN — Deployment Guide

Ubuntu 22.04/24.04 сервер дээр **backend + frontend + nginx + media folder**-ийг
эхнээс нь хэрхэн босгох step-by-step заавар.

> **Энэ заавар нь:** `your-domain.mn` хэмээх домэйн (эсвэл IP `202.70.34.58`)
> дээр Django backend-ийг `:8000` port-д, Next.js frontend-ийг `:3000` port-д
> асаагаад nginx-ээр reverse proxy + media файл serve хийхэд зориулагдсан.

---

## 0. Сервер бэлтгэх (root эсвэл sudo эрхтэй хэрэглэгчээр)

```bash
sudo apt update && sudo apt upgrade -y

# Системийн packages
sudo apt install -y \
    python3 python3-venv python3-pip python3-dev \
    postgresql postgresql-contrib \
    nginx \
    git curl \
    build-essential libpq-dev \
    tesseract-ocr tesseract-ocr-mon \
    libjpeg-dev zlib1g-dev

# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# PM2 (Node-ийн процессыг alive байлгана)
sudo npm install -g pm2

# Тестээр шалгах
python3 --version    # 3.10+
node --version       # v20+
psql --version       # 15+
nginx -v
```

---

## 1. PostgreSQL баазыг үүсгэх

```bash
sudo -u postgres psql
```

Доторх PostgreSQL shell дотор:

```sql
CREATE DATABASE kosen;
CREATE USER kosen_user WITH PASSWORD 'CHANGE_ME_strong_password';
ALTER ROLE kosen_user SET client_encoding TO 'utf8';
ALTER ROLE kosen_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kosen_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE kosen TO kosen_user;
ALTER DATABASE kosen OWNER TO kosen_user;
\q
```

---

## 2. Backend (Django) суулгах

```bash
# Аппын кодыг тавих газар
sudo mkdir -p /var/www
cd /var/www

# Repo татах (token эсвэл https authentication ашиглана)
sudo git clone https://github.com/bilguun2026/kosenBack.git
sudo chown -R $USER:$USER kosenBack
cd kosenBack

# Virtualenv
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn          # production server

# .env үүсгэх
cp .env.example .env
nano .env
```

### `.env` файлд бөглөх утгууд (production):

```env
DEBUG=False
SECRET_KEY=GENERATE_LONG_RANDOM_STRING_HERE
ALLOWED_HOSTS=your-domain.mn,www.your-domain.mn,202.70.34.58

DB_NAME=kosen
DB_USER=kosen_user
DB_PASSWORD=CHANGE_ME_strong_password
DB_HOST=localhost
DB_PORT=5432

# Media: энэ folder-руу бүх uploads (CKEditor зурагнууд, banner-ууд) хадгалагдана.
# Server-ийн өөр диск/volume дээр байлгахыг хүсвэл бүтэн зам бичнэ (доороос харна уу).
MEDIA_ROOT=media
CKEDITOR_5_UPLOAD_PATH=uploads/
```

> **SECRET_KEY үүсгэх (бэлэн команд):**
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

### Migrate + collectstatic + superuser

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Тест: 1 удаа гар аргаар асаах

```bash
python manage.py runserver 0.0.0.0:8000
```

Browser-аар `http://SERVER-IP:8000/api/carousel/` → JSON хариу ирэх ёстой.
Ctrl+C дарж унтраа.

---

## 3. Media folder — externally хадгалах (заавал биш, гэхдээ зөв арга)

Production-д media файлууд app-ийн folder дотор биш, **сервер дээрх тусдаа
volume/disk дээр** байх нь зүйтэй (backup, дискний хэмжээ, app-ийг redeploy
хийсэн ч media файлууд үлддэг).

### Сонголт A — App folder дотор үлдээх (хамгийн энгийн)

```env
MEDIA_ROOT=media
```

→ `/var/www/kosenBack/media/` дотор хадгалагдана. Тэр folder-ийн backup-ыг
гар аргаар авна.

### Сонголт B — Тусдаа disk/volume дээр

```bash
# Disk-ээ хаана mount хийсэн бэ, тэр зам руу шилжүүлнэ
sudo mkdir -p /mnt/media/kosen
sudo chown -R $USER:$USER /mnt/media/kosen

# Хуучин файлуудаа байгаа бол шилжүүлэх
sudo mv /var/www/kosenBack/media/* /mnt/media/kosen/ 2>/dev/null || true
```

Дараа нь `.env`-д **БҮТЭН ЗАМ** бичнэ:

```env
MEDIA_ROOT=/mnt/media/kosen
```

> ⚠ `MEDIA_ROOT`-ийг `/`-ээр эхлэвэл Django үүнийг absolute path гэж үздэг,
> үгүй бол `BASE_DIR`-аас эхлэн relative гэж үздэг. Settings.py дотор аль
> аль нь зөв ажиллахаар бэлэн (29-р мөр: `BASE_DIR / config("MEDIA_ROOT", default="media")`).

### Сонголт C — S3/object storage руу

`django-storages` сонгож хэрэглэх. Энэ зааварт хамаагүй.

---

## 4. Gunicorn-оор backend асаах (systemd service)

```bash
sudo nano /etc/systemd/system/kosen-backend.service
```

Доторх агуулга:

```ini
[Unit]
Description=Kosen Django backend (gunicorn)
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/kosenBack
EnvironmentFile=/var/www/kosenBack/.env
ExecStart=/var/www/kosenBack/venv/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8000 \
  --access-logfile /var/log/kosen-backend-access.log \
  --error-logfile /var/log/kosen-backend-error.log \
  base.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Зөвшөөрөл өгөх + асаах:

```bash
# www-data folder-ыг уншиж/бичих эрхтэй болгох
sudo chown -R www-data:www-data /var/www/kosenBack
sudo chown -R www-data:www-data /mnt/media/kosen   # B сонголт хэрэглэсэн бол

sudo systemctl daemon-reload
sudo systemctl enable kosen-backend
sudo systemctl start kosen-backend
sudo systemctl status kosen-backend     # active (running) гэж харагдах ёстой
```

Алдаа гарвал:
```bash
sudo journalctl -u kosen-backend -f
```

---

## 5. Frontend (Next.js) суулгах

```bash
cd /var/www
sudo git clone https://github.com/bilguun2026/kosenFront.git
sudo chown -R $USER:$USER kosenFront
cd kosenFront

# Dependencies
npm install

# .env үүсгэх
cp .env.example .env
nano .env
```

### `.env` файлд бөглөх утгууд (production):

```env
NEXT_PUBLIC_API_URL=https://your-domain.mn/api
NEXT_PUBLIC_MEDIA_URL=https://your-domain.mn
NEXT_PUBLIC_SITE_URL=https://your-domain.mn
NEXT_PUBLIC_APP_NAME=MUST KOOSEN
SECRET_TOKEN=any-random-string
```

> ⚠ **`NEXT_PUBLIC_*` env-ийг өөрчилсөн бол ЗААВАЛ `npm run build`-ыг дахин ажиллуулна.**
> Тэдгээр утгууд build-ийн үед JS bundle руу шууд оруулагддаг.

### Build + PM2-оор асаах

```bash
npm run build

# PM2-аар порт 3000 дээр асаах
pm2 start npm --name "kosen-frontend" -- start
pm2 save
pm2 startup    # терминалд гарсан команд-ыг хуулж sudo-той дахин ажиллуулна
```

Шалгах:
```bash
pm2 status
pm2 logs kosen-frontend --lines 50
curl http://127.0.0.1:3000      # HTML ирэх ёстой
```

---

## 6. Nginx — reverse proxy + media serve

```bash
sudo nano /etc/nginx/sites-available/kosen
```

Доторх агуулга:

```nginx
# HTTP → HTTPS redirect (SSL суусны дараа идэвхждэг)
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.mn www.your-domain.mn;

    # Let's Encrypt-д хэрэгтэй
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.mn www.your-domain.mn;

    # SSL (certbot босгосны дараа өөрчилөгдөнө)
    ssl_certificate     /etc/letsencrypt/live/your-domain.mn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.mn/privkey.pem;

    client_max_body_size 50M;   # CKEditor зураг, PDF upload-уудад

    # ----- Django static (admin css/js) -----
    location /static/ {
        alias /var/www/kosenBack/staticfiles/;
        expires 30d;
        access_log off;
    }

    # ----- MEDIA (CKEditor uploads, banner зурагнууд) -----
    # MEDIA_ROOT-ыг хаашаа сонгосноосоо хамаарч `alias` зам солих
    location /media/ {
        alias /mnt/media/kosen/;   # эсвэл /var/www/kosenBack/media/
        expires 30d;
        access_log off;

        # Optional: protected file types-ыг блок хийх
        location ~* \.(php|sh|py|exe)$ {
            deny all;
        }
    }

    # ----- Django API + admin -----
    location ~ ^/(api|admin|swagger|redoc|ckeditor5)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # ----- Next.js frontend (бусад бүх зам) -----
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Next.js HMR / image optimization
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Symlink + reload:

```bash
sudo ln -s /etc/nginx/sites-available/kosen /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t        # config зөв эсэхийг шалгана
sudo systemctl reload nginx
```

---

## 7. SSL сертификат (Let's Encrypt — үнэгүй)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.mn -d www.your-domain.mn
```

Certbot:
- Cert-ийг автоматаар үүсгэнэ
- Nginx config-ыг шинэчилнэ
- Auto-renewal-ыг systemd timer-аар тохируулна

Шалгах:
```bash
sudo certbot renew --dry-run
```

---

## 8. Firewall (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

> ⚠ Backend port 8000, frontend port 3000-уудыг **firewall-аар хаах** — зөвхөн
> nginx 80/443 дамжуулна. PostgreSQL-ийг 5432 портоор public-руу гарга**гүй**.

---

## 9. Шинэчлэх (deploy update)

Дараа кодоо update хийхэд:

### Backend update
```bash
cd /var/www/kosenBack
sudo -u www-data git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart kosen-backend
```

### Frontend update
```bash
cd /var/www/kosenFront
git pull
npm install
npm run build
pm2 restart kosen-frontend
```

---

## 10. Backup стратеги (хамгийн чухал!)

### Database backup (өдөр бүр)

```bash
sudo nano /usr/local/bin/kosen-db-backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR=/var/backups/kosen
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
PGPASSWORD='kosen_user-password' pg_dump -U kosen_user -h localhost kosen \
  | gzip > $BACKUP_DIR/kosen-db-$DATE.sql.gz
# 30 хоногоос хуучин backup-уудыг устгана
find $BACKUP_DIR -name "kosen-db-*.sql.gz" -mtime +30 -delete
```

```bash
sudo chmod +x /usr/local/bin/kosen-db-backup.sh
sudo crontab -e
# Доорх мөрийг нэмж өдөр бүр 3 цагт автоматаар ажиллуулна
0 3 * * * /usr/local/bin/kosen-db-backup.sh
```

### Media backup

```bash
# rsync-ээр өөр сервер рүү синк хийх (хамгийн найдвартай)
rsync -av --delete /mnt/media/kosen/ backup-server:/backups/kosen-media/
```

---

## 11. Common debug commands

```bash
# Backend
sudo systemctl status kosen-backend
sudo journalctl -u kosen-backend -f
tail -f /var/log/kosen-backend-error.log

# Frontend
pm2 status
pm2 logs kosen-frontend --lines 100

# Nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Database
sudo -u postgres psql kosen
\dt              # хүснэгтүүдийг харах
\q

# Хэн ямар порт сонссон бэ?
sudo ss -tlnp
```

---

## 12. Checklist (deploy-ийн өмнө 1 удаа дамжуулна)

- [ ] **PostgreSQL** аса, бааз болон user үүсгэсэн
- [ ] **Backend .env** бөглөсөн (DEBUG=False, SECRET_KEY шинэ, DB credentials, ALLOWED_HOSTS зөв)
- [ ] **`python manage.py migrate`** алдаагүй ажилласан
- [ ] **`python manage.py createsuperuser`** хийсэн
- [ ] **`collectstatic`** ажилласан (`staticfiles/` folder үүссэн)
- [ ] **MEDIA_ROOT** folder байгаа, www-data эрхтэй
- [ ] **kosen-backend systemd service** active гэж харагдаж байна
- [ ] `curl http://127.0.0.1:8000/api/carousel/` JSON буцаана
- [ ] **Frontend .env** бөглөсөн (NEXT_PUBLIC_* бүгд real domain руу заасан)
- [ ] **`npm run build`** алдаагүй гүйцэгсэн
- [ ] **PM2** kosen-frontend асаасан, `pm2 save` дарсан
- [ ] **Nginx** config зөв (nginx -t тестээр pass), reload хийсэн
- [ ] **SSL** certbot-оор босгосон, HTTPS-ээр нэвтэрч байна
- [ ] **UFW** firewall enabled
- [ ] **Backup cronjob** crontab дотор орсон
- [ ] Browser-аар `https://your-domain.mn` нээгдэж, carousel, news, content/[id] бүгд харагдаж байна
- [ ] Browser-аар admin (`https://your-domain.mn/admin/`) нэвтэрч, мэдээ оруулж шалгасан
- [ ] Шинэ мэдээний зураг frontend-д харагдаж байна (`https://your-domain.mn/media/...` ажиллаж байна)
- [ ] FB share button дарахад preview зөв гарч ирж байна (production URL дээр)

---

## 13. Хамгийн түгээмэл алдаанууд + засвар

| Алдаа | Шалтгаан + засвар |
|-------|--------------------|
| `500 Server Error` (admin/api) | `DEBUG=False` үед `ALLOWED_HOSTS`-д domain нэмсэн эсэхийг шалгана. `sudo journalctl -u kosen-backend -f` |
| Зураг харагдахгүй (404 on /media/) | Nginx `location /media/` дотор `alias` зам нь `.env`-ийн `MEDIA_ROOT`-той таарч байгаа эсэх, folder permissions `www-data:www-data` мөн эсэх |
| FB share preview хоосон | `NEXT_PUBLIC_SITE_URL` + `NEXT_PUBLIC_MEDIA_URL`-ийг бодит public domain-руу заасан эсэх, build-ийг дахин хийсэн эсэх |
| CSS алга (admin) | `python manage.py collectstatic` дахин гүйцэгэх + nginx `/static/` alias шалгах |
| `connection refused` (gunicorn) | `sudo systemctl status kosen-backend` шалгах, log-ыг үзэх |
| `502 Bad Gateway` (nginx) | gunicorn/PM2 process унтарсан. systemctl restart хийнэ |
| CKEditor зураг upload алдаа | `CKEDITOR_5_UPLOAD_PATH` + `MEDIA_ROOT` folder permissions; nginx `client_max_body_size` хэт жижиг байна |

---

**Амжилт хүсье. 🚀**

Асуулт гарвал dev-руугаа холбогдоорой эсвэл `sudo journalctl -xe` гэж лог үзээрэй.
