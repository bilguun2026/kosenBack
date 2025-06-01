import uuid
from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    TEMPLATE_CHOICES = [
        ('standard', 'Standard'),
        ('homepage', 'Homepage'),
        ('contact', 'Contact'),
        ('admissions', 'Admissions'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    template = models.CharField(
        max_length=50, choices=TEMPLATE_CHOICES, default='standard')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent page, if any"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Content(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='contents')
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name='contents', null=True, blank=True,)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    isPage = models.BooleanField(
        default=False, help_text="Indicates if this content is a page or not")
    isCarousel = models.BooleanField(
        default=False, help_text="Indicates if this content is a carousel or not")

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentImage(models.Model):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='content_images/')
    text = models.TextField(
        blank=True, help_text="Description or caption for the image")
    order = models.IntegerField(default=0, help_text="Order of display")

    class Meta:
        ordering = ['order']

    def __str__(self):
        # Fixed reference to content
        return f"Image for {self.content.title} ({self.order})"


class ContentText(models.Model):  # Renamed to ContentText (singular)
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='texts')
    text = models.TextField(blank=True, help_text="Text content")
    order = models.IntegerField(default=0, help_text="Order of display")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Text for {self.content.title} ({self.order})"
