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

## 4. Тестлэх

Админ хуудсанд орж, контент үүсгэх форм дотор **📄 PDF / Word импортлох** товчийг дарж PDF файл сонгоно. Алдаагүй текст харагдвал амжилттай.

---

## Алдаа гарвал

| Алдаа | Шийдэл |
|-------|--------|
| `tesseract is not installed or it's not in your PATH` | `sudo apt install -y tesseract-ocr` дахин ажиллуулна, `which tesseract` шалгана (`/usr/bin/tesseract` гарах ёстой) |
| `Error opening data file ... mon.traineddata` | Монгол хэлний package дутуу: `sudo apt install -y tesseract-ocr-mon` |
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
