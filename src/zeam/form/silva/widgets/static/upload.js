
(function($) {

    function basename(path) {
        return path.replace(/^.*[\/\\](.*)/, '$1');
    }

    var default_options = {
        stat_url: '/gp.fileupload.stat/',
        stat_timeout: 5000,
        stat_delay: 500,
        max_retries: 3,
        errors: {
            too_many_retries: 'unknown error while uploading file.',
            file_too_big: 'upload failed file is too big.'
        }
    };

    var FileUploader = function($progress, options){
        var deferred = $.Deferred();
        var progress_value = 0;
        var retries = 0;

        var upload_id = Math.random() * 10000000000000000000;
        var timeout = null;

        var form = null;

        options = $.extend(default_options, options);

        var clear_status = function() {
            if (timeout !== null) {
                clearTimeout(timeout);
                timeout = null;
            };
        };

        var set_progress = function(value) {
            if (progress_value != value) {
                progress_value = value;
                $progress.progressbar('option', 'value', value);
            }
        };

        var abort_upload = function(message) {
            clear_status();
            deferred.reject({filename: null, message: message});
        };

        var poll_status = function() {
            clear_status();
            timeout = setTimeout(
                function() {
                    var url = (options.stat_url +
                               upload_id +
                               '?q=' + (Math.random() * 1000000000000000000));
                    $.ajax({
                        type: 'GET',
                        dataType: 'json',
                        timeout: options.stat_timeout,
                        url: url,
                        success: function(data) {
                            switch (data.state) {
                            case -1:
                                abort_upload(options.errors.file_too_big);
                                break;
                            case 0:
                                // not started
                                retries += 1;
                                if (retries > options.max_retries) {
                                    abort_upload(options.errors.too_many_retries);
                                    return;
                                };
                                poll_status();
                                break;
                            case 1:
                                // dl in progress
                                retries = 0;
                                if (data.percent > 0) {
                                    set_progress(data.percent);
                                };
                                if (data.percent < 100) {
                                    poll_status();
                                };
                                break;
                            };
                        },
                        error: function() {
                            retries += 1;
                            if (retries > options.max_retries) {
                                abort_upload(options.errors.too_many_retries);
                                return;
                            }
                            poll_status();
                        }
                    });
                }, options.stat_delay);
        };

        return {
            get_form: function(target, action) {
                var sep = '?';

                form = $('<form class="upload-form"' +
                         'enctype="multipart/form-data"' +
                         'method="POST"' +
                         'action=""' +
                         'target="' + target + '">' +
                         '<input type="file" name="file" />' +
                         '</form>');
                if (action.match(/\?/))
                    sep = "&";
                form.attr('action', action + sep + 'gp.fileupload.id=' + upload_id);
                return form;
            },
            send: function() {
                if (form === null) {
                    return null;
                };
                // listen to event triggered by the iframe, that will
                // mark the end of a successful upload
                $(document).one('done-' + String(upload_id) + '-upload', function(event, data) {
                    deferred.resolve({filename: data.path});
                });
                form.submit();
                poll_status();
                return deferred.promise();
            }
        };
    };

    var create_upload_field = function() {
        var $field = $(this);

        var $upload_button = $field.find('a.upload-trigger');
        var $clear_button = $field.find('a.upload-clear');

        var $progress = $field.find('.upload-progress');
        var $input = $field.find('.upload-input');
        var $status = $field.find('.upload-display');

        var previous_value = $input.val();

        var set_input_value = function(data) {
            if (data.filename) {
                $status.text(basename(data.filename));
            } else if (data.message) {
                $status.text(data.message);
            } else {
                $status.text('not set.');
            };
            $input.val(data.filename);
            $input.change();
        };

        var disable_upload_button = function() {
            $progress.progressbar({value: 0});
            $progress.show();
            $upload_button.button('disable');
            $upload_button.hide();
        };

        var enable_upload_button = function() {
            $progress.hide();
            $upload_button.button('enable');
            $upload_button.show();
        };

        // Support for clear button
        $clear_button.bind('click', function(){
            set_input_value('');
        });

        // Support for upload button
        $upload_button.bind('click', function(){
            var $iframe = $field.find('iframe');
            var $popup = $field.find('.upload-popup').clone();
            var uploader = FileUploader($progress);
            var promise = null;

            $popup.dialog({
                title: $upload_button.text(),
                modal: true,
                create: function() {
                    $popup.find('p').append(
                        uploader.get_form(
                            $iframe.attr('name'), $upload_button.attr('href')));
                },
                autoOpen: false,
                buttons: {
                    Send: function(event){
                        disable_upload_button();
                        promise = uploader.send().fail(
                            function (data) {
                                // failure
                                $field.trigger(
                                    'notify-feedback-smi',
                                    {message: data.message, category: 'error'});
                            }).always(function (data) {
                                // in any case
                                set_input_value(data);
                                enable_upload_button();
                                $popup.remove();
                            });
                        $popup.dialog('close');
                    }
                }
            });
            $popup.bind('dialogclose', function() {
                // the user click on close.
                if (promise === null) {
                    $popup.remove();
                }
            });
            $popup.dialog('open');
        });

    };

    $('form').live('load-smiform', function() {
        $(this).find('.upload-file').each(create_upload_field);
    });

    $(document).ready(function() {
        $('.upload-file').each(create_upload_field);
    });


})(jQuery);
