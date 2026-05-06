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

    function addImportButton(textareaId, ckEditor) {
        if (ckEditor.previousElementSibling && ckEditor.previousElementSibling.classList.contains('doc-import-wrapper')) return;

        var wrapper = document.createElement('div');
        wrapper.className = 'doc-import-wrapper';
        wrapper.style.cssText = 'margin-bottom: 6px;';

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = '📄 PDF / Word импортлох';
        btn.style.cssText = [
            'padding: 5px 12px',
            'background: #417690',
            'color: #fff',
            'border: none',
            'border-radius: 4px',
            'cursor: pointer',
            'font-size: 12px',
            'font-family: inherit',
        ].join(';');

        var fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.docx';
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

            fetch('/api/import-document/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body: formData,
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.error) {
                        alert('Алдаа: ' + data.error);
                        return;
                    }
                    if (!data.html) return;

                    // django-ckeditor-5 stores instances in window.editors keyed by textarea id
                    if (window.editors && window.editors[textareaId]) {
                        window.editors[textareaId].setData(data.html);
                    } else {
                        // Fallback: set the textarea value directly
                        var ta = document.getElementById(textareaId);
                        if (ta) ta.value = data.html;
                    }
                })
                .catch(function (e) { alert('Импортлоход алдаа гарлаа: ' + e.message); })
                .finally(function () {
                    btn.textContent = originalText;
                    btn.disabled = false;
                    fileInput.value = '';
                });
        });

        wrapper.appendChild(btn);
        wrapper.appendChild(fileInput);
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
