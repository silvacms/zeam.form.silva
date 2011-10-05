

(function($, infrae) {

    /**
     * Inline validation on a form.
     */
    var create_validator = function() {
        var $field = $(this);
        if ($field.hasClass('form-novalidation')) {
            return;
        };
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

                    if (($input.is(':checkbox') || $input.is(':radio')) &&
                        !$input.is(':checked')) {
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
                if (status) {
                    $(this).attr('checked', status);
                } else {
                    $(this).removeAttr('checked');
                };
            });
        });

        // Inline Validation
        $form.find('.form-section').each(create_validator);
    };


    $(document).bind('load-smiplugins', function(event, smi) {

        /**
         * Popup form.
         */
        var Popup = function($popup, url) {
            var popup = {};
            var ready = false;

            var create_callback = function($form, form_url, data) {
                var action_label = data['label'];
                var action_name = data['name'];
                var action_type = data['action'];

                return function() {
                    switch (action_type) {
                    case 'send':
                    case 'close_on_success':
                        var form_array = $form.serializeArray();
                        var form_data = {};

                        form_data[action_name] = action_label;
                        for (var j=0; j < form_array.length; j++) {
                            form_data[form_array[j]['name']] = form_array[j]['value'];
                        };

                        // Send request
                        smi.ajax.query(form_url, form_data).pipe(
                            function(data) {
                                if (infrae.interfaces.is_implemented_by('popup', data)) {
                                    if (action_type == 'close_on_success' && data['success']) {
                                        if (data['refresh']) {
                                            var identifier = data['refresh'];
                                            $('form[name="' + identifier + '"]').trigger('refresh-smi');
                                        };
                                        popup.close();
                                    } else {
                                        bootstrap_form(popup.from_data(data));
                                    };
                                    return data;
                                };
                                popup.close();
                                return $(document).render({data: data, args: [smi]});
                            });
                        break;
                    case 'close':
                        popup.close();
                        break;
                    };
                    return false;
                };
            };

            $.extend(popup, {
                display: function(builder) {
                    return $.when(builder).done(function ($form) {
                        // Initialize form and widgets JS, show the popup
                        $form.trigger('load-smiform');
                        infrae.ui.ShowDialog($popup);
                    });
                },
                close: function() {
                    $popup.dialog('close');
                },
                from_url: function() {
                    return smi.ajax.query(url).pipe(
                        popup.from_data,
                        function (request) {
                            // In case of error, close the popup (to
                            // trigger the cleaning), return an reject
                            // not to display it.
                            popup.close();
                            return $.Deferred().reject(request);
                        });
                },
                from_data: function(data) {
                    var $form = $('<form />');
                    var buttons = {};

                    $popup.dialog('option', 'title', data['label']);
                    $popup.empty();
                    $popup.append($form);
                    $form.attr('data-form-url', url);
                    $form.attr('name', data.prefix);
                    $form.html(data['widgets']);
                    // Add an empty input submit to activate form submission with enter
                    $form.append('<input type="submit" style="display: none" />');
                    for (var i=0; i < data['actions'].length; i++) {
                        var label = data['actions'][i]['label'];
                        var callback = create_callback($form, data.form_url || url, data['actions'][i]);

                        buttons[label] = callback;
                        if (data['actions'][i]['name'] == data['default_action']) {
                            $form.bind('submit', callback);
                        };
                    };
                    $popup.dialog('option', 'buttons', buttons);
                    ready = true;
                    return $form;
                }
            });
            return popup;
        };

        /**
         * Open a Form popup.
         * @param url: if not undefined, the url for form.
         */
        $.fn.SMIFormPopup = function(options) {
            var $popup = $('<div></div>');

            $popup.dialog({
                autoOpen: false,
                modal: true,
                width: 800
            });
            // When the popup is closed, clean its HTML and bindings
            $popup.bind('dialogclose', function() {
                $popup.remove();
            });

            // Create a popup from a builder
            var url = undefined;
            if (options !== undefined && options.url !== undefined) {
                url = options.url;
                if (options.payload !== undefined) {
                    url += '?' + $.param(options.payload);
                };
            } else {
                url = $(this).attr('href');
            };
            var popup = new Popup($popup, url);
            var builder = null;
            if (infrae.interfaces.is_implemented_by('popup', options)) {
                builder = popup.from_data(options);
            } else {
                builder = popup.from_url();
            };
            popup.display(builder);
            return false;
        };

        // You can create a popup as a view as well
        infrae.views.view({
            iface: 'popup',
            factory: function($content, data) {
                return $content.SMIFormPopup(data);
            }
        });
    });

    // Registeration code: Prepare forms
    $('form').live('load-smiform', bootstrap_form);

    $(document).ready(function() {
        $('.form-content').each(bootstrap_form);

        // Prepare Popup
        $('.form-popup').live('click', function() {
            return $(this).SMIFormPopup();
        });
    });


})(jQuery, infrae);
