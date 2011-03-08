

(function($) {

    /**
     * Inline validation on a form.
     */
    var Validator = function(field) {
        var form = field.closest('form');
        this.field = field;
        this.field_prefix = field.attr('data-field-prefix');
        this.form_prefix = form.attr('name');
        this.form_url = form.attr('data-form-url');

        var validator = this.validate.scope(this);
        this.field.find('.field').bind('change', function () {
            setTimeout(validator, 0);
        });
    };

    Validator.prototype.validate = function() {
        var values = [{name: 'prefix.field', value: this.field_prefix},
                      {name: 'prefix.form', value: this.form_prefix}];

        var serialize_field = function() {
            var input = $(this);
            var add = true;

            if (input.is(':checkbox') && !input.is(':checked')) {
                add = false;
            };
            if (add) {
                values.push({name: input.attr('name'), value: input.val()});
            };
        };

        this.field.find('input').each(serialize_field);
        this.field.find('textarea').each(serialize_field);
        this.field.find('select').each(serialize_field);
        $.ajax({
            url: this.form_url + '/++rest++zeam.form.silva.validate',
            type: 'POST',
            dataType: 'json',
            data: values,
            success: function(data) {
                if (data['success']) {
                    this.clear();
                } else {
                    this.error(data['error']);
                };
            }.scope(this)});

    };

    Validator.prototype.error = function(message) {
        this.field.children('.form-error-detail').remove();
        this.field.addClass('form-error');
        if (message) {
            this.field.append('<div class="form-error-detail"><p>' + message +'</p></div>');
        }
    };

    Validator.prototype.clear = function() {
        this.field.removeClass('form-error');
        this.field.children('.form-error-detail').remove();
    };

    /**
     * Field focus management.
     */
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

        // Inline Validation
        form.find('.form-section').each(function (index) {
            new Validator($(this));
        });
    };

    $('form').live('load-smiform', function() {
        create_form($(this));
    });

    $(document).ready(function() {
        create_form($('.form-content'));
    });


})(jQuery);
