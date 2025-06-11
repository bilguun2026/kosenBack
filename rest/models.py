import uuid
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class Page(models.Model):
    TEMPLATE_CHOICES = [
        ('standard', 'Энгийн'),
        ('homepage', 'Нүүр хуудас'),
        ('contact', 'Холбоо барих'),
        ('admissions', 'Элсэлт'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Гарчиг'
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Дэд гарчиг'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug'
    )
    template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default='standard',
        verbose_name='Загвар'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Нийтлэгдсэн эсэх'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Үүсгэсэн огноо'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Шинэчилсэн огноо'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Эцэг хуудас',
        help_text='Хэрэв энэ нь дэд хуудас бол эцэг хуудсыг сонгоно уу'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Хуудас"
        verbose_name_plural = "Хуудсууд"


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Нэр'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Таг'
        verbose_name_plural = 'Тагууд'


class Content(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Гарчиг'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Тайлбар'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug'
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='contents',
        verbose_name='Тагууд'
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='contents',
        null=True,
        blank=True,
        verbose_name='Холбогдсон хуудас'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name='Үүсгэсэн огноо'
    )
    isPage = models.BooleanField(
        default=False,
        verbose_name='Хуудас эсэх',
        help_text="Энэ контент хуудсан дээр байна уу?"
    )
    isCarousel = models.BooleanField(
        default=False,
        verbose_name='Карусель эсэх',
        help_text="Энэ контент карусель дээр байна уу?"
    )

    class Meta:
        ordering = ['title']
        verbose_name = 'Контент'
        verbose_name_plural = 'Контентууд'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentImage(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Холбогдсон контент'
    )
    image = models.ImageField(
        upload_to='content_images/',
        verbose_name='Зураг'
    )
    text = models.TextField(
        blank=True,
        help_text="Зургийн тайлбар эсвэл гарчиг",
        verbose_name='Тайлбар'
    )
    order = models.IntegerField(
        default=0,
        help_text="Дараалал",
        verbose_name='Жагсаалтын дараалал'
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'Контентийн зураг'
        verbose_name_plural = 'Контентийн зургууд'

    def __str__(self):
        return f"{self.content.title} - Зураг #{self.order}"


class ContentText(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='texts',
        verbose_name='Холбогдсон контент'
    )
    text = CKEditor5Field(
        'Текст агуулга',
        config_name='extends'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Жагсаалтын дараалал'
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'Контентийн текст'
        verbose_name_plural = 'Контентийн текстүүд'

    def __str__(self):
        return f"{self.content.title} - Текст #{self.order}"


class VideoUrl(models.Model):
    title = models.CharField(
        max_length=200,
        help_text="Видеогийн гарчиг",
        verbose_name="Гарчиг"
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Гадаад видеогийн холбоос (YouTube, Facebook гэх мэт)",
        verbose_name='Видео холбоос'
    )
    video_file = models.FileField(
        upload_to='videos/',
        blank=True,
        null=True,
        help_text="Видео файл оруулах (mp4, webm гэх мэт)",
        verbose_name='Видео файл'
    )

    def __str__(self):
        return self.title or "Нэргүй видео"

    @property
    def video_source(self):
        if self.video_file:
            return self.video_file.url
        return self.url

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видеонууд'
