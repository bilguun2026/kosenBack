# rest/views.py
import io
import re
from collections import Counter
import mammoth
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from django.views import View
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ImportantURL, Page, Tag, Content, ContentImage, ContentText, VideoUrl
from .serializers import (
    ContentListSerializer, ImportantURLSerializer, PageSerializer, TagSerializer, ContentSerializer,
    ContentImageSerializer, ContentTextSerializer, PageNavigationSerializer, VideoSerializer
)


class ReadOnlyOrAdminPermission(IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user and request.user.is_staff


class PageNavigationViewSet(viewsets.ReadOnlyModelViewSet):
    # Only top-level published pages
    queryset = Page.objects.filter(is_published=True, parent__isnull=True)
    serializer_class = PageNavigationSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template']
    search_fields = ['title']
    ordering_fields = ['title']
    ordering = ['title']

    def get_queryset(self):
        return Page.objects.filter(is_published=True, parent__isnull=True).prefetch_related('children')


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'is_published', 'parent']
    search_fields = ['title', 'subtitle']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']

    def get_queryset(self):
        return Page.objects.prefetch_related('contents__tags', 'contents__images', 'contents__texts', 'children')


# Rest of the viewsets (unchanged)
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tags__slug']  # Allow ?tags__name=School
    search_fields = ['title']  # Disable ?search=
    ordering_fields = ['title', 'page', 'created_at']
    ordering = ['title']

    def get_queryset(self):
        queryset = Content.objects.select_related(
            'page').prefetch_related('tags', 'images', 'texts')
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ContentListSerializer
        return ContentSerializer


class ContentImageViewSet(viewsets.ModelViewSet):
    queryset = ContentImage.objects.all()
    serializer_class = ContentImageSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['content']
    search_fields = ['text']
    ordering_fields = ['order', 'content']
    ordering = ['order']


class ContentTextViewSet(viewsets.ModelViewSet):
    queryset = ContentText.objects.all()
    serializer_class = ContentTextSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['content']
    search_fields = ['text']
    ordering_fields = ['order', 'content']
    ordering = ['order']


class CarouselContentListView(generics.ListAPIView):
    queryset = Content.objects.filter(isCarousel=True)
    serializer_class = ContentSerializer


class VideoViewSet(ReadOnlyModelViewSet):
    queryset = VideoUrl.objects.all()
    serializer_class = VideoSerializer


class ImportantURLViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ImportantURLSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return ImportantURL.objects.filter(is_active=True).order_by("order", "title")


@method_decorator(staff_member_required, name='dispatch')
class ImportDocumentView(View):
    def post(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return JsonResponse({'error': 'No file provided'}, status=400)

        name = uploaded.name.lower()
        try:
            if name.endswith('.docx'):
                html = self._docx_to_html(uploaded)
            elif name.endswith('.pdf'):
                html = self._pdf_to_html(uploaded)
            else:
                return JsonResponse({'error': 'Only .pdf and .docx files are supported'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'html': html})

    def _docx_to_html(self, file):
        result = mammoth.convert_to_html(file)
        return result.value

    def _pdf_to_html(self, file):
        parts = []
        doc = fitz.open(stream=file.read(), filetype='pdf')
        for page in doc:
            raw = page.get_text('dict', flags=fitz.TEXT_PRESERVE_WHITESPACE)
            text_blocks = [b for b in raw.get('blocks', []) if b.get('type') == 0]

            if text_blocks:
                # Detect table bounding boxes so we skip those blocks below
                table_bboxes = []
                try:
                    for tbl in page.find_tables().tables:
                        table_bboxes.append(fitz.Rect(tbl.bbox))
                        parts.append(self._table_to_html(tbl))
                except Exception:
                    pass

                body_size = self._body_font_size(text_blocks)

                for block in text_blocks:
                    # Skip blocks that fall inside a table area
                    block_rect = fitz.Rect(block['bbox'])
                    if any(block_rect.intersects(tr) for tr in table_bboxes):
                        continue
                    html = self._block_to_html(block, body_size)
                    if html:
                        parts.append(html)
            else:
                # Image-based page — OCR with Mongolian + English
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img, lang='mon+eng')
                for line in ocr_text.split('\n'):
                    line = line.strip()
                    if line:
                        parts.append(f'<p>{line}</p>')

        doc.close()
        return ''.join(parts)

    # ------------------------------------------------------------------ helpers

    def _body_font_size(self, text_blocks):
        sizes = [
            round(span['size'])
            for block in text_blocks
            for line in block.get('lines', [])
            for span in line.get('spans', [])
            if span.get('text', '').strip()
        ]
        return Counter(sizes).most_common(1)[0][0] if sizes else 12

    def _span_to_html(self, span):
        text = span.get('text', '')
        if not text.strip():
            return text  # preserve spaces

        flags = span.get('flags', 0)
        font = span.get('font', '').lower()
        is_bold = bool(flags & 16) or 'bold' in font
        is_italic = bool(flags & 2) or 'italic' in font or 'oblique' in font

        if is_bold:
            text = f'<strong>{text}</strong>'
        if is_italic:
            text = f'<em>{text}</em>'
        return text

    def _block_to_html(self, block, body_size):
        spans_flat = [
            span
            for line in block.get('lines', [])
            for span in line.get('spans', [])
            if span.get('text', '').strip()
        ]
        if not spans_flat:
            return ''

        avg_size = sum(s['size'] for s in spans_flat) / len(spans_flat)

        # Build content line by line
        line_htmls = []
        for line in block.get('lines', []):
            inline = ''.join(self._span_to_html(s) for s in line.get('spans', []))
            if inline.strip():
                line_htmls.append(inline.strip())

        if not line_htmls:
            return ''

        content = ' '.join(line_htmls)
        first_line = line_htmls[0]

        # Heading detection by relative font size
        if avg_size >= body_size * 1.8:
            return f'<h2>{content}</h2>'
        if avg_size >= body_size * 1.4:
            return f'<h3>{content}</h3>'
        if avg_size >= body_size * 1.15:
            return f'<h4>{content}</h4>'

        # Unordered list item
        if re.match(r'^[•·\-–*]\s', first_line):
            item = re.sub(r'^[•·\-–*]\s*', '', content)
            return f'<ul><li>{item}</li></ul>'

        # Ordered list item  (1. / 1) / a. etc.)
        if re.match(r'^(\d+[\.\)]|[a-zA-Z][\.\)])\s', first_line):
            item = re.sub(r'^[\w]+[\.\)]\s*', '', content)
            return f'<ol><li>{item}</li></ol>'

        return f'<p>{content}</p>'

    def _table_to_html(self, tbl):
        rows = tbl.extract()
        if not rows:
            return ''
        html = ['<figure class="table"><table><tbody>']
        for i, row in enumerate(rows):
            html.append('<tr>')
            tag = 'th' if i == 0 else 'td'
            for cell in row:
                cell_text = (cell or '').strip()
                html.append(f'<{tag}>{cell_text}</{tag}>')
            html.append('</tr>')
        html.append('</tbody></table></figure>')
        return ''.join(html)
