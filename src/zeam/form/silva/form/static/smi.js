

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

    $(document).bind('load-smiplugins', function(event, smi) {

        /**
         * Popup form.
         */
        var Popup = function($popup, extra_array) {
            var popup = {};
            var ready = false;
            var popup_close = $.Deferred();

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
                        if (extra_array !== undefined) {
                            for (j=0; j < extra_array.length; j++) {
                                form_data[extra_array[j]['name']] = extra_array[j]['value'];
                            };
                        };

                        // Send request
                        smi.ajax.query(form_url, form_data).pipe(
                            function(data) {
                                if (infrae.interfaces.is_implemented_by('popup', data)) {
                                    if (action_type == 'close_on_success' && data['success']) {
                                        return popup.close(data);
                                    };
                                    return popup.from_data(data);
                                };
                                return popup.close(data).done(function(data) {
                                    return $(document).render({data: data, args: [smi]});
                                });
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
                $popup.remove();
            });

            $.extend(popup, {
                display: function(builder) {
                    return $.when(builder).pipe(
                        function ($form) {
                            // Initialize form and widgets JS, show the popup
                            infrae.ui.ShowDialog($popup);
                            return popup;
                        },
                        function (request) {
                            // Request failed.
                            return $.Deferred().reject(request);
                        });
                },
                close: function(data) {
                    $popup.dialog('close');
                    return popup_close.resolve(data);
                },
                promise: function() {
                    return popup_close.promise();
                },
                from_url: function(url) {
                    return smi.ajax.query(url).pipe(
                        popup.from_data,
                        function (request) {
                            // In case of error, close the popup (to
                            // trigger the cleaning), return an reject
                            // not to display it.
                            $popup.dialog('close');
                            return popup_close.reject(request);
                        });
                },
                from_data: function(data) {
                    var $form = $('<form class="form-fields-container" />');
                    var buttons = {};

                    $form.attr('data-form-url', data.url);
                    $form.attr('name', data.prefix);
                    $form.html(data['widgets']);
                    // Add an empty input submit to activate form submission with enter
                    $form.append('<input type="submit" style="display: none" />');
                    // Set the dialog content
                    $popup.dialog('option', 'title', data['label']);
                    $popup.empty();
                    $popup.append($form);
                    for (var i=0; i < data['actions'].length; i++) {
                        var label = data['actions'][i]['label'];
                        var callback = create_callback($form, data.url, data['actions'][i]);

                        buttons[label] = callback;
                        if (data['actions'][i]['name'] == data['default_action']) {
                            $form.bind('submit', callback);
                        };
                    };
                    $popup.dialog('option', 'buttons', buttons);
                    $form.trigger('load-smiform', {form: $form, container: $form});
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
            var $popup = $('<div class="form-content"></div>');

            // Create a popup from a builder
            var url = undefined;
            options = $.extend(options, {});
            if (options.url !== undefined) {
                url = options.url;
            } else {
                url = $(this).attr('href');
            };
            var popup = new Popup($popup, options.payload);
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
    $('.field-collection-line').live('addline-zeamform', function() {
        var $line = $(this);

        $line.addClass('form-fields-container');
        $line.trigger('loadwidget-smiform');
    });
    $('.form-fields-container').live('loadwidget-smiform', function(event) {
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

        // Inline Validation
        $form.find('.form-section').each(create_validator);
    };

    // Registeration code: Prepare forms
    $('.form-content').live('load-smiform', bootstrap_form);

    $(document).ready(function() {
        $('.form-content').each(bootstrap_form);

        // Prepare Popup
        $('.form-popup').live('click', function() {
            $(this).SMIFormPopup();
            return false;
        });
    });


})(jQuery, infrae);
