# Ubuntu сервер дээр Tesseract OCR (Монгол хэлтэй) суулгах заавар

PDF/зураг бичигдсэн файлыг текст рүү хөрвүүлэхэд `tesseract` хэрэгтэй. Дараах командуудыг сервер дээрээ ажиллуулна уу.

---

## 1. Tesseract + Монгол + Англи хэлний багц суулгах

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-mon tesseract-ocr-eng
```

- `tesseract-ocr` — үндсэн OCR хөдөлгүүр
- `tesseract-ocr-mon` — **Монгол хэлний plugin (заавал шаардлагатай)**
- `tesseract-ocr-eng` — Англи хэлний plugin

---

## 2. Суулгасан эсэхийг шалгах

```bash
tesseract --version
```

Гаралт нь иймэрхүү байх ёстой:

```
tesseract 5.x.x
 leptonica-1.x.x
```

Монгол + Англи хэл бэлэн байгаа эсэхийг шалгах:

```bash
tesseract --list-langs
```

Жагсаалт дотор **`mon`** ба **`eng`** хоёулаа байх ёстой:

```
List of available languages...:
eng
mon
osd
```

---

## 3. Django сервер дахин ачаалах

Tesseract суулгасны дараа Django serverэ дахин ачаалаагүй бол PDF импорт хийх үед `tesseract is not installed` гэсэн алдаа гарсаар байх болно.

```bash
sudo systemctl restart kosenback.service     # эсвэл өөрийн сервисийн нэр
```

---

## 3.1 Gunicorn timeout-ийг нэмэгдүүлэх (ЗААВАЛ)

OCR хийх (зурган PDF) ажиллагаа 1–5 минут үргэлжилж болзошгүй. Gunicorn-ийн анхдагч timeout нь 30 секунд тул боловсруулалт дуусахаас өмнө worker-ийг таслаж **500 алдаа** буцаана. Лог дотор `handle_abort` ба `SystemExit: 1` гарч ирвэл энэ нь яг тэр асуудал.

### Алхам 1: Өөрийн gunicorn service файлыг олох

Service-ийн нэр тус бүр өөр өөр байж болно (`kosenback`, `gunicorn`, эсвэл бусад). Эхлээд олно:

```bash
sudo systemctl list-units --type=service | grep -iE 'gunicorn|kosen'
```

Гарсан нэрийг тэмдэглэж аваад service файлд хандана (жишээ нь `gunicorn.service`):

```bash
sudo systemctl cat gunicorn.service     # одоогийн агуулгыг харна
sudo nano /etc/systemd/system/gunicorn.service
```

### Алхам 2: Одоо байгаа `ExecStart=` мөрөнд `--timeout 300` НЭМНЭ

> ⚠️ **Анхааруулга**: Бүх мөрийг солих хэрэггүй. Өөрийн серверт байгаа замуудаа (venv, socket) **хэвээр нь үлдээх ёстой**, зөвхөн `--timeout 300` гэдгийг нэмнэ.

**Жишээ нь, одоо ийм байж магадгүй:**

```ini
ExecStart=/home/youruser/path/to/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          base.wsgi:application
```

**Үүнийг ийм болгож засна** (зөвхөн `--timeout 300` мөр нэмэгдсэн):

```ini
ExecStart=/home/youruser/path/to/venv/bin/gunicorn \
          --timeout 300 \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          base.wsgi:application
```

### Алхам 3: Сервисийг дахин ачаалах

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.service       # эсвэл өөрийн service-ийн нэр
sudo systemctl status gunicorn.service        # `active (running)` байх ёстой
```

### Алхам 4: Nginx-ийн timeout-ийг мөн нэмэгдүүлнэ (504 алдаа гарахаас сэргийлнэ)

```bash
sudo nano /etc/nginx/sites-available/<your-site>
```

`location /` блок дотор дараах мөрийг нэмнэ (хэрэв байхгүй бол):

```nginx
location / {
    include proxy_params;
    proxy_pass http://unix:/run/gunicorn.sock;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

Тестлэх ба reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 4. Тестлэх

Админ хуудсанд орж, контент үүсгэх форм дотор **📄 PDF / Word импортлох** товчийг дарж PDF файл сонгоно. Алдаагүй текст харагдвал амжилттай.

---

## Алдаа гарвал

| Алдаа | Шийдэл |
|-------|--------|
| `tesseract is not installed or it's not in your PATH` | `sudo apt install -y tesseract-ocr` дахин ажиллуулна, `which tesseract` шалгана (`/usr/bin/tesseract` гарах ёстой) |
| `Error opening data file ... mon.traineddata` | Монгол хэлний package дутуу: `sudo apt install -y tesseract-ocr-mon` |
| `500 Internal Server Error` + лог дотор `handle_abort`, `SystemExit: 1` | Gunicorn worker timeout. `--timeout 300` нэмнэ (3.1-р хэсгийг үзнэ үү) |
| `504 Gateway Time-out` | Nginx-ийн `proxy_read_timeout` богино. 300s болгож нэмэгдүүлнэ (3.1-р хэсэг) |
| Текст танигдсан боловч муухай гарч байна | PDF нь чанар муутай зурагт байна. Хариу хэвлэгдсэн эсвэл скан хийсэн чанар сайтай PDF ашиглана уу |

---

## Хэрэгцээтэй командуудын лавлагаа

```bash
# Tesseract хувилбар
tesseract --version

# Боломжтой хэлүүд
tesseract --list-langs

# Tesseract байршил
which tesseract       # /usr/bin/tesseract байх ёстой

# Хэлний файлуудын байршил
ls /usr/share/tesseract-ocr/*/tessdata/    # mon.traineddata, eng.traineddata байх ёстой
```
