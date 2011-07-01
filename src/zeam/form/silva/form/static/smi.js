

(function($) {

    /**
     * Inline validation on a form.
     */
    var create_validator = function() {
        var $field = $(this);
        var $form = $field.closest('form');
        var field_prefix = $field.attr('data-field-prefix');
        var form_prefix = $form.attr('name');
        var form_url = $form.attr('data-form-url');

        if (!form_url) {
            return;
        };

        $field.find('.field').bind('change', function () {
            setTimeout(function() {
                var values = [{name: 'prefix.field', value: field_prefix},
                              {name: 'prefix.form', value: form_prefix}];

                var serialize_field = function() {
                    var $input = $(this);
                    var add = true;

                    if ($input.is(':checkbox') && !$input.is(':checked')) {
                        add = false;
                    };
                    if (add) {
                        values.push({name: $input.attr('name'), value: $input.val()});
                    };
                };

                $field.find('input').each(serialize_field);
                $field.find('textarea').each(serialize_field);
                $field.find('select').each(serialize_field);
                $.ajax({
                    url: form_url + '/++rest++zeam.form.silva.validate',
                    type: 'POST',
                    dataType: 'json',
                    data: values,
                    success: function(data) {
                        var $container = $field.children('.form-field');

                        if (data['success']) {
                            // Success, clear the errors
                            $field.removeClass('form-error');
                            $container.children('.form-error-detail').remove();
                        } else {
                            // Report error
                            $field.addClass('form-error');
                            $container.children('.form-error-detail').remove();
                            if (data['error']) {
                                $container.prepend(
                                    '<div class="form-error-detail"><p>' + data['error'] +'</p></div>');
                            };
                        };
                    }
                });
            }, 0);
        });
    };

    /**
     * Bootstrap javascript helper for forms.
     */
    var bootstrap_form = function() {
        var $form = $(this);

        // Select all
        $form.find('.zeam-select-all').bind('change', function() {
            var $select = $(this);
            var status = $select.attr('checked');
            $form.find('.' + $select.attr('name')).each(function() {
                $(this).attr('checked', status);
            });
        });

        // Inline Validation
        $form.find('.form-section').each(create_validator);
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
        var form = $('form[name="' + identifier + '"]');
        form.trigger('refresh-smi');
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
                    if (data.notifications) {
                        this.popup.trigger('notify-feedback-smi', data.notifications);
                    };
                    if (action_type == 'close_on_success' && data['success']) {
                        if (data['refresh']) {
                            this._refresh(data['refresh']);
                        };
                        this.close();
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
    };

    Popup.prototype.update = function(data) {
        var $form = $('<form />');
        var buttons = {};

        this.popup.dialog('option', 'title', data['label']);
        this.popup.empty();
        this.popup.append($form);
        $form.attr('data-form-url', this.url);
        $form.attr('name', data.prefix);
        $form.append(data['widgets']);
        // Add an empty input submit to activate form submission with enter
        $form.append('<input type="submit" style="display: none" />');
        for (var i=0; i < data['actions'].length; i++) {
            var label = data['actions'][i]['label'];
            var callback = this._create_callback($form, data['actions'][i]);
            buttons[label] = callback;
            if (data['actions'][i]['name'] == data['default_action']) {
                $form.bind('submit', callback);
            };
        };
        this.popup.dialog('option', 'buttons', buttons);
        return $form;
    };

    Popup.prototype.display = function() {
        this.popup.bind('dialogclose', function() {
            this.popup.remove();
        }.scope(this));
        $.getJSON(this.url, function(data) {
            var $form = this.update(data);
            this.popup.dialog('open');
            // Initialize form and widgets JS.
            $form.trigger('load-smiform');
        }.scope(this));
    };

    /**
     * Open a Form popup.
     * @param url: if not undefined, the url for form.
     */
    $.fn.SMIFormPopup = function(url) {
        var $popup = $('#form-popup');
        if (!$popup.length) {
            $popup= $('<div id="form-popup"></div>');
        };
        if (url == undefined) {
            url = $(this).attr('href');
        };
        $popup.dialog({
            autoOpen: false,
            modal: true,
            width: 800
        });
        var form = new Popup($popup, url);
        form.display();
        return false;
    };

    // Registeration code: Prepare forms
    $('form').live('load-smiform', bootstrap_form);

    $(document).ready(function() {
        $('.form-content').each(bootstrap_form);

        // Prepare Popup
        $('.form-popup').live('click', function() {
            return $(this).SMIFormPopup();
        });
    });


})(jQuery);
