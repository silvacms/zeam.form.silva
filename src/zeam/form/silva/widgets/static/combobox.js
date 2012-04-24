(function($) {

    var create_combobox_field = function() {
        var $field = $(this);
        var $select = $field.children('select');
        var $input = $field.children('input.combobox-input');
        var $opener = $field.children('a.combobox-opener');

	    var selected = $select.children(":selected");
	    var value = selected.val() ? selected.text() : "";

		$input.val(value).autocomplete({
			delay: 0,
			minLength: 0,
			source: function(request, response) {
				var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
				response($select.children("option").map(function() {
					var text = $(this).text();
					if (this.value && (!request.term || matcher.test(text)))
						return {
							label: text.replace(
								new RegExp(
									"(?![^&;]+;)(?!<[^<>]*)(" +
										$.ui.autocomplete.escapeRegex(request.term) +
										")(?![^<>]*>)(?![^&;]+;)", "gi"
								), "<strong>$1</strong>" ),
							value: text,
							option: this
						};
				}));
			},
			select: function(event, ui) {
				ui.item.option.selected = true;
                value = ui.item.value;
			},
			change: function(event, ui) {
				if (!ui.item) {
                    var valid = false;
					var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex($(this).val()) + "$", "i");
					$select.children("option").each(function() {
                        var $option = $(this);

						if ($option.text().match(matcher)) {
							this.selected = valid = true;
							return false;
						}
					});
					if (!valid) {
						// Clean invalid value, set original back one.
						$(this).val(value);
						$select.val(value);
						$input.data("autocomplete").term = value;
						return false;
					}
				}
			}
		});

		$input.data("autocomplete")._renderItem = function(ul, item) {
			return $("<li><a>" + item.label + "</a></li>")
				.data("item.autocomplete", item)
				.appendTo(ul);
		};
		$opener.click(function() {
			// close if already visible
			if ($input.autocomplete("widget").is(":visible") ) {
				$input.autocomplete("close");
				return;
			};

			$opener.blur();
			$input.autocomplete("search", "");
			$input.focus();
		});
    };

    $('.form-fields-container').live('loadwidget-smiform', function(event) {
        $(this).find('.field-combobox').each(create_combobox_field);
        event.stopPropagation();
    });

    $(document).ready(function() {
        $('.field-combobox').each(create_combobox_field);
    });

})(jQuery);
