(function () {
  function getSelectedType() {
    var checked = document.querySelector('input[name="content_type"]:checked');
    return checked ? checked.value : null;
  }

  function clearTags() {
    var tagsSelect = document.getElementById('id_tags');
    if (!tagsSelect) return;

    if (tagsSelect.tagName === 'SELECT' && tagsSelect.multiple) {
      for (var i = 0; i < tagsSelect.options.length; i++) {
        tagsSelect.options[i].selected = false;
      }
    }
  }

  function clearPage() {
    var pageSelect = document.getElementById('id_page');
    if (pageSelect) {
      pageSelect.value = '';
    }
  }

  function clearCarousel() {
    var chk = document.getElementById('id_isCarousel');
    if (chk && chk.type === 'checkbox') {
      chk.checked = false;
    }
  }

  function toggleFields() {
    var value = getSelectedType();

    // ----- page field -----
    var pageRow =
      document.querySelector('.form-row.field-page') ||
      document.querySelector('.field-page');
    if (pageRow) {
      pageRow.style.display = (value === 'page') ? '' : 'none';
    }

    if (value !== 'page') {
      clearPage();
    }

    // ----- tags field + its fieldset -----
    var tagsRow =
      document.querySelector('.form-row.field-tags') ||
      document.querySelector('.field-tags');

    if (tagsRow) {
      var tagsFieldset = tagsRow.closest('fieldset');
      var showTags = (value === 'news');

      tagsRow.style.display = showTags ? '' : 'none';
      if (tagsFieldset) {
        tagsFieldset.style.display = showTags ? '' : 'none';
      }

      if (!showTags) {
        clearTags();
      }
    }

    // ----- carousel field -----
    var carouselRow =
      document.querySelector('.form-row.field-isCarousel') ||
      document.querySelector('.field-isCarousel');

    if (carouselRow) {
      var showCarousel = (value === 'news');
      carouselRow.style.display = showCarousel ? '' : 'none';

      if (!showCarousel) {
        clearCarousel();
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    toggleFields();
    var radios = document.querySelectorAll('input[name="content_type"]');
    radios.forEach(function (radio) {
      radio.addEventListener('change', toggleFields);
    });
  });
})();
