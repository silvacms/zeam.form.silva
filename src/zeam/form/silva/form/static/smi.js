
(function($, infrae) {

    /**
     * Inline validation on a form.
     */
    var create_validator = function() {
        var $field = $(this);

        if ($field.hasClass('form-novalidation')) {
            return;
        };
        if ($field.closest('.field-object').length) {
            return;             // We ignore fields in objects
        };
        var $form = $field.closest('form');
        var field_prefix = $field.attr('data-field-prefix');
        var form_prefix = $form.attr('name');
        var form_url = $form.attr('data-form-url');

        if (!form_url) {
            return;
        };

        var find_sub_field = function(selector) {
            if (!$field.is(selector)) {
                return $field.find(selector).children('div.form-field');
            };
            return $field.children('div.form-field');
        };

        $field.delegate('.field', 'change', function () {
            setTimeout(function() {
                var values = [{name: 'prefix.field', value: field_prefix},
                              {name: 'prefix.form', value: form_prefix}];

                var serialize_field = function() {
                    var $input = $(this);

                    if (($input.is(':checkbox') || $input.is(':radio')) &&
                        !$input.is(':checked')) {
                        return;
                    };
                    var value = $input.val();

                    if (value === null) {
                        return;
                    } else if (!$.isArray(value)) {
                        value = [value];
                    };
                    for (var i=value.length; i > 0; i--) {
                        values.push({name: $input.attr('name'), value: value[i - 1]});
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
                        var key, errors = data['errors'];
                        $field.find('.form-error-message').remove();

                        if (data['success']) {
                            // Success, clear the errors
                            $field.removeClass('form-error');
                            return;
                        };
                        // Report error
                        $field.addClass('form-error');
                        if (errors) {
                            for (key in errors) {
                                find_sub_field('div[data-field-prefix="' + key + '"]').after(
                                    '<div class="form-error-message"><div class="form-error-detail"><p>' + errors[key] +'</p></div></div>');
                            };
                        };
                    }
                });
            }, 0);
        });
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        /**
         * Popup form.
         */
        var Popup = function($popup, extra_array) {
            var popup = {};
            var close = $.Deferred();
            var closing = false;
            var $form = null;

            var cleanup_form = function() {
                if ($form !== null) {
                    $form.trigger('clean-smiform', {form: $form, container: $form, popup: $popup});
                    $form.remove();
                    $form = null;
                };
            };

            var create_callback = function(form_url, data) {
                var action_label = data['label'];
                var action_name = data['name'];
                var action_type = data['action'];

                return function() {
                    switch (action_type) {
                    case 'send':
                    case 'close_on_success':
                        $form.trigger('serialize-smiform',
                                      {form: $form, container: $form, popup: $popup});
                        var form_data = $form.serializeArray();

                        form_data.push({name: action_name, value: action_label});
                        if (extra_array !== undefined) {
                            form_data = form_data.concat(extra_array);
                        };

                        // Send request
                        smi.ajax.query(form_url, form_data).then(
                            function(data) {
                                if (infrae.interfaces.is_implemented_by('popup', data)) {
                                    if (action_type == 'close_on_success' && data['success']) {
                                        return popup.close(data);
                                    };
                                    return $.when(popup.from_data(data)).then(function ($form) {
                                        infrae.ui.ResizeDialog($popup);
                                        return $form;
                                    });
                                };
                                return popup.close(data).done(function(data) {
                                    return $(document).render({data: data, args: [smi]});
                                });
                            }, function(request) {
                                // On error, just close the popup.
                                popup.close({});
                            });
                        break;
                    case 'close':
                        popup.close({});
                        break;
                    };
                    return false;
                };
            };

            $popup.dialog({
                autoOpen: false,
                modal: true,
                width: 800
            });
            // When the popup is closed, clean its HTML and bindings
            $popup.bind('dialogclose', function() {
                cleanup_form();
                $popup.remove();
                // If closing is false, that means the user closed the
                // popup by clicking on the close on top of the popup.
                if (closing === false) {
                    close.reject({});
                };
            });
            $popup.delegate('a.open-screen', 'click', function(event) {
                $popup.dialog('close');
            });

            $.extend(popup, {
                display: function(builder) {
                    return $.when(builder).then(
                        function ($form) {
                            // Initialize form and widgets JS, show the popup
                            infrae.ui.ShowDialog($popup, {maxFactor: 0.8});
                            return popup;
                        },
                        function (request) {
                            // Request failed.
                            return $.Deferred().reject(request);
                        });
                },
                close: function(data) {
                    closing = true;
                    $popup.dialog('close');
                    return close.resolve(data);
                },
                promise: function() {
                    return close.promise();
                },
                from_url: function(url) {
                    return smi.ajax.query(url).then(
                        function (data) {
                            if (infrae.interfaces.is_implemented_by('popup', data)) {
                                return popup.from_data(data);
                            };
                            return popup.close(data);
                        },
                        function (request) {
                            // In case of error, close the popup (to
                            // trigger the cleaning), return an reject
                            // not to display it.
                            closing = true;
                            $popup.dialog('close');
                            return close.reject(request);
                        });
                },
                from_data: function(data) {
                    var buttons = {};
                    var submit_url = data.submit_url || data.url;

                    // Start by cleaning any existing form
                    cleanup_form();
                    $form = $('<form class="form-content form-fields-container" />');
                    $form.attr('data-form-url', data.url);
                    if (!data.validation) {
                        $form.attr('data-form-novalidation', 'true');
                    };
                    $form.attr('name', data.prefix);
                    $form.html(data['widgets']);
                    // Add an empty input submit to activate form submission with enter
                    $form.append('<input type="submit" style="display: none" />');
                    // Set the dialog content
                    $popup.dialog('option', 'title', data['label']);
                    $popup.append($form);
                    for (var i=0; i < data['actions'].length; i++) {
                        var label = data['actions'][i]['label'];
                        var callback = create_callback(submit_url, data['actions'][i]);

                        buttons[label] = callback;
                        if (data['actions'][i]['name'] == data['default']) {
                            $form.bind('submit', callback);
                        };
                    };
                    $popup.dialog('option', 'buttons', buttons);
                    $form.trigger('load-smiform', {form: $form, container: $form, popup: $popup});
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

            // Create a popup from a builder
            var url = undefined;
            options = $.extend(options, {});
            if (options.url !== undefined) {
                url = options.url;
            } else {
                url = $(this).attr('href');
            };
            var popup = Popup($popup, options.payload);
            var builder = null;
            if (infrae.interfaces.is_implemented_by('popup', options)) {
                builder = popup.from_data(options);
            } else {
                builder = popup.from_url(url);
            };
            return popup.display(builder);
        };

        // You can create a popup as a view as well
        infrae.views.view({
            iface: 'popup',
            factory: function($content, data) {
                return $content.SMIFormPopup(data);
            }
        });
    });

    // Support for collection widget
    $(document).on('addline-zeamform', '.field-collection-line', function() {
        var $line = $(this);

        $line.addClass('form-fields-container');
        $line.trigger('loadwidget-smiform');
    });
    $(document).on('loadwidget-smiform', '.form-fields-container', function(event) {
        $(this).find('div.field-collection').each(function() {
            if ($(this).ZeamCollectionWidget !== undefined) {
                $(this).ZeamCollectionWidget();
            };
        });
        event.stopPropagation();
    });

    // Bootstrap form
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

        // Invalid Validation on the form.
        if ($form.is('form') && ! $form.data('form-novalidation')) {
            $form.find('.form-section').each(create_validator);
        };

        // Inline Validation on the sub-forms.
        $form.find('form').each(function() {
            var $form = $(this);

            if (!$form.data('form-novalidation')) {
                $form.find('.form-section').each(create_validator);
            };

        });
    };

    // Prepare forms
    $(document).on('load-smiform', '.form-content', bootstrap_form);

    $(document).ready(function() {
        $('.form-content').each(bootstrap_form);

        // Prepare Popup
        $(document).on('click', '.form-popup', function() {
            $(this).SMIFormPopup();
            return false;
        });
    });

})(jQuery, infrae);
