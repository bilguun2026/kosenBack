(function ($) {
  $(document).ready(function () {
    // Make inlines sortable
    $(".inline-related").each(function () {
      $(this).sortable({
        items: "tr:has(.field-order)",
        handle: ".field-order",
        update: function (event, ui) {
          // Update order fields after sorting
          $(this)
            .find("tr:has(.field-order)")
            .each(function (index) {
              $(this)
                .find('input[id$="-order"]')
                .val(index + 1);
            });
        },
      });
    });

    // Add visual feedback for draggable rows
    $(".inline-related tr:has(.field-order)").css("cursor", "move");

    // Ensure new inline forms get correct order
    $(document).on("formset:added", function (event, $row, formsetName) {
      var maxOrder = 0;
      $row
        .closest(".inline-related")
        .find('input[id$="-order"]')
        .each(function () {
          var order = parseInt($(this).val()) || 0;
          if (order > maxOrder) maxOrder = order;
        });
      $row.find('input[id$="-order"]').val(maxOrder + 1);
    });
  });
})(django.jQuery);
