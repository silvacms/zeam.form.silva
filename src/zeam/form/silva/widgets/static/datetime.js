
(function($) {

    var create_datetime_field = function() {
        var $field = $(this);

        if ($field.attr('readonly') == 'readonly') {
            // No picker for readonly fields.
            return;
        };

        var id = $field.attr('id');
        var $year = $('#' + id + '-year');
        var $month = $('#' + id + '-month');
        var $day = $('#' + id + '-day');
        var $hour = $('#' + id + '-hour');
        var $minute = $('#' + id + '-min');
        var $remove = $('#' + id + '-remove');
        var hasTime = ($hour.length > 0);
        var lang = $(document).find('html').attr('lang');

        var field_settings = {
            showOn: 'button',
            // XXX need to figure out something to get image with JS
            buttonImage: '/++static++/zeam.form.silva.widgets/calendar.png',
            buttonImageOnly: true,
            buttonText: 'Date picker',
            showWeek: true,
            showOtherMonths: true,
            dateFormat: 'yy/mm/dd',
            onSelect: function(date, picker) {
                var parts = date.split('/');

                $day.val(parts[2]);
                $month.val(parts[1]);
                $year.val(parts[0]);
                if (hasTime) {
                    if (!$hour.val()) {
                        $hour.val('00');
                    };
                    if (!$minute.val()) {
                        $minute.val('00');
                    };
                }
                $field.trigger('change');
            },
            beforeShow: function() {
                var selected_day = $day.val();
                var selected_month = $month.val();
                var selected_year = $year.val();
                var date = null;

                if (selected_day && selected_month && selected_year) {
                    date = new Date(selected_year, selected_month - 1, selected_day);
                } else {
                    date = new Date();
                };
                $field.datepicker('setDate', date);
            }
        };
        if ($remove.length) {
            $remove.bind('click', function(event) {
                // Reset everything
                $day.val('');
                $month.val('');
                $year.val('');
                if (hasTime) {
                    $hour.val('');
                    $minute.val('');
                }
                $field.datepicker('setDate', new Date());
                return false;
            });
        };

        var lang_settings = $.datepicker.regional[lang];
        if (!lang_settings) {
            lang_settings = $.datepicker.regional[''];
        };
        $field.datepicker($.extend({}, lang_settings, field_settings));
    };

    if (window.smi !== undefined) {
        $(document).on('loadwidget-smiform', '.form-fields-container', function(event) {
            $(this).find('.field-datetime, .field-date').each(create_datetime_field);
            event.stopPropagation();
        });
    } else {
        // This widget can be used on the public view as well.
        $(document).ready(function() {
            $(this).find('.field-datetime, .field-date').each(create_datetime_field);
        });
    };

})(jQuery);
