(function($, infrae) {

    var create_combobox_field = function() {
        var $field = $(this);
        var $select = $field.children('select');
        var $input = $field.children('input.combobox-input');
        var $opener = $field.children('a.combobox-opener');

	    var selected = $select.children(":selected");
	    var value = selected.text();

		$input.val(value).autocomplete({
			delay: 0,
			minLength: 0,
			source: function(request, response) {
				var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
				response($select.children("option").map(function() {
                    var $option = $(this);
					var text = $option.text();

					if (!request.term || matcher.test(text)) {
						return {
							label: text.replace(
								new RegExp(
									"(?![^&;]+;)(?!<[^<>]*)(" +
										$.ui.autocomplete.escapeRegex(request.term) +
										")(?![^<>]*>)(?![^&;]+;)", "gi"
								), "<strong>$1</strong>" ),
                            icon: $option.data('combobox-icon'),
							value: text,
							option: this
						};
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

        $input.data("autocomplete")._resizeMenu = function() {
		    var $ul = this.menu.element;
            // 20 pixels to let place for icon, 20 for scroll bar
		    $ul.outerWidth( Math.max(
			    $ul.width( "" ).outerWidth() + 40,
			    this.element.outerWidth()
		    ) );
	    };

		$input.data("autocomplete")._renderItem = function(ul, item) {
            var $item = $('<li><a>' + item.label + "</a></li>");

            if (item.icon) {
                var $icon = $('<ins class="icon" />');

                infrae.ui.icon($icon, item.icon);
                $item.prepend($icon);
            };
			return $item.data("item.autocomplete", item).appendTo(ul);
		};
        $input.autocomplete('widget').zIndex($input.zIndex() + 1);
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

    $(document).on('loadwidget-smiform', '.form-fields-container', function(event) {
        $(this).find('.field-combobox').each(create_combobox_field);
        event.stopPropagation();
    });

})(jQuery, infrae);
