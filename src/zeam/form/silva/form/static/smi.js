

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

        if (!this.form_url) {
            return;
        };

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

    var bootstrap_form = function(form) {
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

    /**
     * Popup form.
     */

    var Popup = function(popup, url) {
        this.popup = popup;
        this.url = url;
    };

    Popup.prototype._send = function(form_data, callback) {
        $.ajax({
            url: this.url,
            type: 'POST',
            dataType: 'json',
            data: form_data,
            success: callback
        });
    };

    Popup.prototype._refresh = function(identifier) {
        $.getJSON(
            document.location + '/++rest++form-refresh',
            {'identifier': identifier},
            function (data) {
                $('#' + identifier).replaceWith(data['form']);
                this.close();
            }.scope(this));
    };

    Popup.prototype._create_callback = function(form, data) {
        var action_label = data['label'];
        var action_name = data['name'];
        var action_type = data['action'];
        return function() {
            if (action_type == 'send' || action_type == 'close_on_success') {
                var form_array = form.serializeArray();
                var form_data = {};
                form_data[action_name] = action_label;
                for (var j=0; j < form_array.length; j++) {
                    form_data[form_array[j]['name']] = form_array[j]['value'];
                };
                this._send(form_data,  function(data) {
                    if (action_type == 'close_on_success' && data['success']) {
                        if (data['refresh']) {
                            this._refresh(data['refresh']);
                        } else {
                            this.close();
                        };
                    } else {
                        bootstrap_form(this.update(data));
                    };
                }.scope(this));
            };
            if (action_type == 'close') {
                this.close();
            };
            return false;
        }.scope(this);
    };

    Popup.prototype.close = function() {
        this.popup.dialog('close');
        this.popup.empty();
        $(document).trigger('refresh-feedback-smi');
    };

    Popup.prototype.update = function(data) {
        var form = $('<form />');
        var buttons = {};

        this.popup.dialog('option', 'title', data['label']);
        this.popup.empty();
        this.popup.append(form);
        form.attr('data-form-url', this.url);
        form.attr('name', data.prefix);
        form.append(data['widgets']);
        // Add an empty input submit to activate form submission with enter
        form.append($('<input type="submit" style="display: none" />'));
        for (var i=0; i < data['actions'].length; i++) {
            var label = data['actions'][i]['label'];
            var callback = this._create_callback(form, data['actions'][i]);
            buttons[label] = callback;
            if (data['actions'][i]['name'] == data['default_action']) {
                form.bind('submit', callback);
            };
        };
        this.popup.dialog('option', 'buttons', buttons);
        return form;
    };

    Popup.prototype.display = function() {
        $.getJSON(this.url, function(data) {
            var form = this.update(data);
            this.popup.dialog('open');
            bootstrap_form(form);
        }.scope(this));
    };

    $('form').live('load-smiform', function() {
        bootstrap_form($(this));
    });

    $(document).ready(function() {
        bootstrap_form($('.form-content'));

        // Prepare Popup
        $('.form-popup').live('click', function() {
            var url = $(this).attr('href');
            var popup = $('#form-popup');
            if (!popup.length) {
                popup= $('<div id="form-popup"></div>');
            };
            popup.dialog({
                autoOpen: false,
                modal: true,
                width: 800
            });
            var form = new Popup(popup, url);
            form.display();
            return false;
        });
    });


})(jQuery);
