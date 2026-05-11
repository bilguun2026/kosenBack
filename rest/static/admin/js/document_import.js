(function () {
    'use strict';

    function getCsrfToken() {
        var cookie = document.cookie.split(';').find(function (c) {
            return c.trim().startsWith('csrftoken=');
        });
        if (cookie) return cookie.split('=')[1];
        var input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    var BTN_STYLE = [
        'padding: 5px 12px',
        'background: #417690',
        'color: #fff',
        'border: none',
        'border-radius: 4px',
        'cursor: pointer',
        'font-size: 12px',
        'font-family: inherit',
        'margin-right: 6px',
    ].join(';');

    function buildButton(label, accept, endpoint, mode, textareaId) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = label;
        btn.style.cssText = BTN_STYLE;

        var fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = accept;
        fileInput.style.display = 'none';

        btn.addEventListener('click', function () { fileInput.click(); });

        fileInput.addEventListener('change', function () {
            var file = this.files[0];
            if (!file) return;

            var originalText = btn.textContent;
            btn.textContent = 'Импортлож байна...';
            btn.disabled = true;

            var formData = new FormData();
            formData.append('file', file);

            fetch(endpoint, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body: formData,
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.error) { alert('Алдаа: ' + data.error); return; }
                    if (!data.html) return;

                    if (window.editors && window.editors[textareaId]) {
                        var editor = window.editors[textareaId];
                        if (mode === 'append') {
                            // Append rather than replace so editors can mix sources.
                            var existing = editor.getData() || '';
                            editor.setData(existing + data.html);
                        } else {
                            editor.setData(data.html);
                        }
                    } else {
                        var ta = document.getElementById(textareaId);
                        if (ta) ta.value = (mode === 'append' ? (ta.value || '') : '') + data.html;
                    }
                })
                .catch(function (e) { alert('Импортлоход алдаа гарлаа: ' + e.message); })
                .finally(function () {
                    btn.textContent = originalText;
                    btn.disabled = false;
                    fileInput.value = '';
                });
        });

        var holder = document.createElement('span');
        holder.appendChild(btn);
        holder.appendChild(fileInput);
        return holder;
    }

    function addImportButton(textareaId, ckEditor) {
        if (ckEditor.previousElementSibling && ckEditor.previousElementSibling.classList.contains('doc-import-wrapper')) return;

        var wrapper = document.createElement('div');
        wrapper.className = 'doc-import-wrapper';
        wrapper.style.cssText = 'margin-bottom: 6px;';

        // Text/style extraction (existing behavior).
        wrapper.appendChild(buildButton(
            '📄 PDF / Word импортлох',
            '.pdf,.docx',
            '/api/import-document/',
            'replace',
            textareaId
        ));

        // New: render each PDF page as an image and insert them into the editor.
        wrapper.appendChild(buildButton(
            '🖼️ PDF-ийг зураг болгох',
            '.pdf',
            '/api/import-pdf-images/',
            'append',
            textareaId
        ));

        ckEditor.parentNode.insertBefore(wrapper, ckEditor);
    }

    function findTextareaIdForEditor(ckEditor) {
        // Walk backwards through siblings to find the textarea CKEditor replaced
        var sibling = ckEditor.previousElementSibling;
        while (sibling) {
            if (sibling.tagName === 'TEXTAREA') return sibling.id;
            sibling = sibling.previousElementSibling;
        }
        // Fallback: look inside the parent container
        var parent = ckEditor.parentElement;
        if (parent) {
            var ta = parent.querySelector('textarea');
            if (ta) return ta.id;
        }
        return null;
    }

    function setupButtons() {
        document.querySelectorAll('.ck.ck-editor').forEach(function (ckEditor) {
            var textareaId = findTextareaIdForEditor(ckEditor);
            if (textareaId) addImportButton(textareaId, ckEditor);
        });
    }

    function waitAndSetup(attempts) {
        attempts = attempts || 0;
        if (attempts > 20) return; // give up after ~10 seconds
        var hasEditors = window.editors && Object.keys(window.editors).length > 0;
        var hasCkDom = document.querySelector('.ck.ck-editor');
        if (hasEditors || hasCkDom) {
            setupButtons();
        }
        // Keep polling — new inlines may be added dynamically
        setTimeout(function () { waitAndSetup(attempts + 1); }, 500);
    }

    document.addEventListener('DOMContentLoaded', function () {
        // Initial setup after editors likely initialized
        setTimeout(function () { waitAndSetup(0); }, 800);

        // Handle dynamically added inline forms
        document.addEventListener('formset:added', function () {
            setTimeout(setupButtons, 800);
        });
    });
})();
