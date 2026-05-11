# rest/views.py
import base64
import html as html_lib
import os
import re
import shutil
import mammoth
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Locate the tesseract binary. Linux/macOS usually have it in PATH; on Windows
# the UB-Mannheim installer drops it into Program Files but doesn't add to PATH.
_tesseract_cmd = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") \
    or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
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
from .models import ImportantURL, InfoCard, Page, Tag, Content, ContentImage, ContentText, VideoUrl
from .serializers import (
    ContentListSerializer, ImportantURLSerializer, InfoCardSerializer, PageSerializer, TagSerializer, ContentSerializer,
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


class InfoCardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InfoCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return InfoCard.objects.filter(is_active=True).order_by("order")


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
        # Embed images as base64 so the editor doesn't lose them, and keep
        # mammoth's default direct-formatting preservation (bold, italic,
        # underline, lists, tables, hyperlinks).
        def _img_handler(image):
            with image.open() as src:
                data = src.read()
            b64 = base64.b64encode(data).decode('ascii')
            return {"src": f"data:{image.content_type};base64,{b64}"}

        # A small style map: keep heading semantics from Word + common emphases.
        style_map = """
        p[style-name='Title'] => h1.doc-title:fresh
        p[style-name='Subtitle'] => h2.doc-subtitle:fresh
        p[style-name='Heading 1'] => h1:fresh
        p[style-name='Heading 2'] => h2:fresh
        p[style-name='Heading 3'] => h3:fresh
        p[style-name='Heading 4'] => h4:fresh
        p[style-name='Quote'] => blockquote > p:fresh
        r[style-name='Strong'] => strong
        r[style-name='Emphasis'] => em
        """
        result = mammoth.convert_to_html(
            file,
            convert_image=mammoth.images.img_element(_img_handler),
            style_map=style_map,
        )
        return result.value

    def _pdf_to_html(self, file):
        parts = []
        doc = fitz.open(stream=file.read(), filetype='pdf')
        for page in doc:
            page_width = page.rect.width
            raw = page.get_text('dict', flags=fitz.TEXT_PRESERVE_WHITESPACE)
            blocks = raw.get('blocks', [])
            text_blocks = [b for b in blocks if b.get('type') == 0]
            image_blocks = [b for b in blocks if b.get('type') == 1]

            if text_blocks or image_blocks:
                # Detect table bounding boxes so we skip those text blocks below
                table_bboxes = []
                try:
                    for tbl in page.find_tables().tables:
                        table_bboxes.append(fitz.Rect(tbl.bbox))
                        parts.append(self._table_to_html(tbl))
                except Exception:
                    pass

                # Render in the order they appear on the page (top-to-bottom, left-to-right).
                renderables = []
                for block in text_blocks:
                    block_rect = fitz.Rect(block['bbox'])
                    if any(block_rect.intersects(tr) for tr in table_bboxes):
                        continue
                    renderables.append((block['bbox'][1], block['bbox'][0], 'text', block))
                for block in image_blocks:
                    renderables.append((block['bbox'][1], block['bbox'][0], 'image', block))
                renderables.sort(key=lambda x: (x[0], x[1]))

                for _y, _x, kind, block in renderables:
                    if kind == 'text':
                        html = self._block_to_html(block, page_width)
                    else:
                        html = self._image_block_to_html(block)
                    if html:
                        parts.append(html)
            else:
                # Fully image-based page (scanned) — fall back to OCR.
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img, lang='mon+eng')
                for line in ocr_text.split('\n'):
                    line = line.strip()
                    if line:
                        parts.append(f'<p>{html_lib.escape(line)}</p>')

        doc.close()
        return ''.join(parts)

    # ------------------------------------------------------------------ helpers

    def _color_to_hex(self, color_int):
        """PyMuPDF color int (0xRRGGBB) → '#rrggbb'."""
        if not color_int:
            return '#000000'
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return f'#{r:02x}{g:02x}{b:02x}'

    def _clean_font_name(self, font):
        """Strip subset prefixes like 'ABCDEF+Arial-Bold' → 'Arial'."""
        if not font:
            return ''
        # Drop subset prefix "ABCDEF+"
        if '+' in font:
            font = font.split('+', 1)[1]
        # Drop weight/style suffix "-Bold", "-Italic", etc.
        font = re.split(r'[-,]', font, maxsplit=1)[0]
        return font.strip()

    def _span_to_html(self, span):
        """Wrap span text in inline-styled <span>, with <strong>/<em>/<u> as needed."""
        raw = span.get('text', '')
        if not raw:
            return ''
        # Preserve whitespace-only spans literally (no styling needed).
        if not raw.strip():
            return html_lib.escape(raw).replace(' ', '&nbsp;')

        text = html_lib.escape(raw)

        flags = span.get('flags', 0)
        font = span.get('font', '') or ''
        font_lower = font.lower()
        # PyMuPDF flag bits: 1=superscript, 2=italic, 4=serif, 8=mono, 16=bold
        is_bold = bool(flags & 16) or any(s in font_lower for s in ('bold', 'black', 'heavy'))
        is_italic = bool(flags & 2) or 'italic' in font_lower or 'oblique' in font_lower
        is_super = bool(flags & 1)

        styles = []
        size = span.get('size')
        if size:
            styles.append(f'font-size:{size:.1f}pt')
        color_hex = self._color_to_hex(span.get('color', 0))
        if color_hex != '#000000':
            styles.append(f'color:{color_hex}')
        clean_font = self._clean_font_name(font)
        if clean_font:
            styles.append(f"font-family:'{clean_font}', sans-serif")

        if styles:
            text = f'<span style="{";".join(styles)}">{text}</span>'
        if is_bold:
            text = f'<strong>{text}</strong>'
        if is_italic:
            text = f'<em>{text}</em>'
        if is_super:
            text = f'<sup>{text}</sup>'
        return text

    def _line_alignment(self, lines, page_width):
        """Detect block alignment by averaging line left/right margins."""
        lefts, rights = [], []
        for line in lines:
            bbox = line.get('bbox')
            if not bbox:
                continue
            lefts.append(bbox[0])
            rights.append(page_width - bbox[2])
        if not lefts:
            return 'left'
        avg_left = sum(lefts) / len(lefts)
        avg_right = sum(rights) / len(rights)
        # Centered: comparable left and right margins, both > 0.
        if abs(avg_left - avg_right) < 8 and avg_left > 20:
            return 'center'
        # Right aligned: large left margin, tiny right margin.
        if avg_right < 8 and avg_left > 40:
            return 'right'
        return 'left'

    def _block_to_html(self, block, page_width):
        lines = block.get('lines', [])
        if not lines:
            return ''

        align = self._line_alignment(lines, page_width)

        # Build line-by-line, preserving original line breaks within the block.
        line_htmls = []
        for line in lines:
            inline = ''.join(self._span_to_html(s) for s in line.get('spans', []))
            if inline.strip():
                line_htmls.append(inline)
        if not line_htmls:
            return ''

        content = '<br>'.join(line_htmls)

        # List detection (only when the block actually starts with a bullet/number).
        first_line_plain = self._strip_tags(line_htmls[0])
        if re.match(r'^[•·▪◦●\-–*]\s', first_line_plain):
            item = re.sub(r'^[•·▪◦●\-–*]\s*', '', content, count=1)
            style = f' style="text-align:{align}"' if align != 'left' else ''
            return f'<ul{style}><li>{item}</li></ul>'
        if re.match(r'^(\d+[\.\)]|[a-zA-Z][\.\)])\s', first_line_plain):
            item = re.sub(r'^[\w]+[\.\)]\s*', '', content, count=1)
            style = f' style="text-align:{align}"' if align != 'left' else ''
            return f'<ol{style}><li>{item}</li></ol>'

        style_attr = f' style="text-align:{align}"' if align != 'left' else ''
        return f'<p{style_attr}>{content}</p>'

    def _strip_tags(self, html_str):
        return re.sub(r'<[^>]+>', '', html_str)

    def _image_block_to_html(self, block):
        """Embed an inline raster image from PyMuPDF as base64."""
        try:
            data = block.get('image')
            if not data:
                return ''
            ext = block.get('ext') or 'png'
            mime = f'image/{ext}'
            b64 = base64.b64encode(data).decode('ascii')
            width = block.get('width') or ''
            height = block.get('height') or ''
            size_attr = ''
            if width and height:
                size_attr = f' width="{int(width)}" height="{int(height)}"'
            return f'<p style="text-align:center"><img src="data:{mime};base64,{b64}"{size_attr} /></p>'
        except Exception:
            return ''

    def _table_to_html(self, tbl):
        rows = tbl.extract()
        if not rows:
            return ''
        # Read styled cells from the first row to seed header detection: a row is
        # treated as a header if every cell is non-empty and short.
        header_idx = 0 if all((c or '').strip() for c in rows[0]) else -1
        html = ['<figure class="table"><table style="border-collapse:collapse;width:100%">']
        if header_idx == 0:
            html.append('<thead><tr>')
            for cell in rows[0]:
                cell_text = html_lib.escape((cell or '').strip())
                html.append(
                    f'<th style="border:1px solid #999;padding:6px;background:#f3f3f3">{cell_text}</th>'
                )
            html.append('</tr></thead>')
        html.append('<tbody>')
        body_rows = rows[1:] if header_idx == 0 else rows
        for row in body_rows:
            html.append('<tr>')
            for cell in row:
                cell_text = html_lib.escape((cell or '').strip()).replace('\n', '<br>')
                html.append(
                    f'<td style="border:1px solid #999;padding:6px;vertical-align:top">{cell_text}</td>'
                )
            html.append('</tr>')
        html.append('</tbody></table></figure>')
        return ''.join(html)
