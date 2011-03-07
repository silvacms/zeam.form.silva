
(function($) {

    var create_datetime_field = function(field) {
        var id = field.attr('id');
        var year = $('#' + id + '-year');
        var month = $('#' + id + '-month');
        var day = $('#' + id + '-day');
        var hour = $('#' + id + '-hour');
        var min = $('#' + id + '-min');
        var lang = $(document).find('html').attr('lang');
        var settings = {};

        var lang_settings = $.datepicker.regional[lang];
        if (!lang_settings) {
            lang_settings = $.datepicker.regional[''];
        };
        for (key in lang_settings) {
            settings[key] = lang_settings[key];
        };
        settings['showOn'] = 'button';
        // XXX need to figure out something to get image with JS
        settings['buttonImage'] = 'calendar.gif';
        settings['showWeek'] = true;
        settings['showOtherMonths'] = true;
        settings['dateFormat'] = 'yy/mm/dd';
        settings['onSelect'] = function(date, picker) {
            var parts = date.split('/');
            day.val(parts[2]);
            month.val(parts[1]);
            year.val(parts[0]);
            if (!hour.val()) {
                hour.val('00');
            };
            if (!min.val()) {
                min.val('00');
            };
        };
        settings['beforeShow'] = function() {
            var selected_day = day.val();
            var selected_month = month.val();
            var selected_year = year.val();
            if (day && month && year) {
                field.datepicker('setDate', new Date(selected_year, selected_month - 1, selected_day));
            };
        };
        field.datepicker(settings);
    };

    $('form').live('load-smiform', function() {
        $(this).find('.field-datetime').each(function(index, field){
            create_datetime_field($(field));
        });
    });

    $(document).ready(function() {
        $('.field-datetime').each(function(index, field){
            create_datetime_field($(field));
        });
    });

})(jQuery);
