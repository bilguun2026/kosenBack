(function () {
  "use strict";

  function getCookie(name) {
    var v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return v ? v.pop() : "";
  }

  function addImportButtons() {
    var editors = document.querySelectorAll(".django_ckeditor_5");
    editors.forEach(function (el) {
      if (el.getAttribute("data-import-btn")) return;
      el.setAttribute("data-import-btn", "1");

      var wrapper = el.closest(".form-row") || el.parentNode;

      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "📂 PDF/Word файлаас оруулах";
      btn.style.cssText =
        "margin:8px 0;padding:8px 16px;background:#2f3a9a;color:#fff;" +
        "border:none;border-radius:6px;cursor:pointer;font-size:14px;";
      btn.onmouseover = function () {
        btn.style.background = "#ffc20c";
        btn.style.color = "#2f3a9a";
      };
      btn.onmouseout = function () {
        btn.style.background = "#2f3a9a";
        btn.style.color = "#fff";
      };

      var fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ".pdf,.docx";
      fileInput.style.display = "none";

      var status = document.createElement("span");
      status.style.cssText = "margin-left:12px;font-size:13px;color:#666;";

      btn.addEventListener("click", function () {
        fileInput.click();
      });

      fileInput.addEventListener("change", function () {
        var file = fileInput.files[0];
        if (!file) return;

        status.textContent = "⏳ Файл уншиж байна...";
        status.style.color = "#2f3a9a";

        var formData = new FormData();
        formData.append("file", file);

        fetch("/import-file/", {
          method: "POST",
          credentials: "same-origin",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: formData,
        })
          .then(function (res) {
            return res.json();
          })
          .then(function (data) {
            if (data.error) {
              status.textContent = "❌ " + data.error;
              status.style.color = "red";
              return;
            }

            var editorInstance = window.editors && window.editors[el.id];
            if (editorInstance) {
              var viewFragment =
                editorInstance.data.processor.toView(data.html);
              var modelFragment =
                editorInstance.data.toModel(viewFragment);
              editorInstance.model.change(function (writer) {
                editorInstance.model.insertContent(modelFragment);
              });
              status.textContent = "✅ Амжилттай оруулсан!";
              status.style.color = "green";
            } else {
              var textarea = document.getElementById(el.id);
              if (textarea) {
                textarea.value = (textarea.value || "") + data.html;
              }
              status.textContent = "✅ Оруулсан (editor олдсонгүй, textarea-д бичив)";
              status.style.color = "orange";
            }

            fileInput.value = "";
          })
          .catch(function (err) {
            status.textContent = "❌ Алдаа: " + err.message;
            status.style.color = "red";
          });
      });

      wrapper.insertBefore(btn, el);
      wrapper.insertBefore(fileInput, el);
      wrapper.insertBefore(status, el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(addImportButtons, 500);
    });
  } else {
    setTimeout(addImportButtons, 500);
  }

  var target = document.body || document.documentElement;
  if (target) {
    var observer = new MutationObserver(function () {
      setTimeout(addImportButtons, 300);
    });
    observer.observe(target, { childList: true, subtree: true });
  }
})();
