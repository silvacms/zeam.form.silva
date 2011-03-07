

(function($) {

    var focus_form_field = function(field) {
        var section = field.closest('.form-section');
        if (section.hasClass('form-focus')) {
            return;
        };
        var form = section.closest('form');
        form.find('.form-section').removeClass('form-focus');
        section.addClass('form-focus');
        section.find('.field:first').focus();
    };

    $('.form-section').live('focusin', function() {
        focus_form_field($(this));
    });

    $('.form-section').live('click', function(){
        focus_form_field($(this));
    });

    var focus_first_form_field = function(form) {
        var field = form.find('.field-error:first').find('.field:first');
        if (field.length) {
            // First error field
            focus_form_field(field);
        } else {
            // Focus first required field otherwise
            field = form.find('.field-required:first');
            focus_form_field(field);
        };
    };

    var create_form = function(form) {
        // Focus
        focus_first_form_field(form);

        // Select all
        form.find('.zeam-select-all').bind('change', function() {
            var select = $(this);
            var status = select.attr('checked');
            form.find('.' + select.attr('name')).each(function() {
                $(this).attr('checked', status);
            });
        });
    };

    $('form').live('load-smiform', function() {
        create_form($(this));
    });

    $(document).ready(function() {
        create_form($('.form-content'));
    });


})(jQuery);
