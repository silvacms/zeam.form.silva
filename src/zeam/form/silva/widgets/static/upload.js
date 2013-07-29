(function($, jsontemplate) {
    var POLL_NETWORK_RETRIES = 5,
        POLL_NETWORK_DELAY = 500,
        POLL_MISSING_RETRIES = 20,
        DONT_NEED_POPUP = (function () {
            // Test if we need a Javascript POPUP to display the file input or not.
            var $test = $('<div style="display:none;"><form id="testform1">' +
                      '<input type="file" form="testform2" /></form><form id="testform2">' +
                      '</form></div>'),
            supported = false;
        $('body').append($test);
        supported = ($test.find('#testform1')[0].length === 0 &&
                     $test.find('#testform2')[0].length === 1);
        $test.remove();
        return supported;
    })();

    /**
     * Status checker report the status of the upload to the uploader.
     */

    var PollStatusChecker = function(url, identifier, result) {
        var poll_retries = POLL_NETWORK_RETRIES,
            poll_timeout = null,
            missing_retries = POLL_MISSING_RETRIES,
            deferred = $.Deferred(),
            poll = function() {
                // Poll status from the server.
                $.ajax({
                    type: 'GET',
                    dataType: 'json',
                    url: url + '?status&identifier=' + identifier
                }).then(function(info){
                    var error = null;

                    result.notify(info);
                    if (info['missing']) {
                        missing_retries -= 1;
                        if (!missing_retries) {
                            error = info['upload-error'] || 'Upload does not start';
                            deferred.reject({message: 'Upload failed ('+ error + ').'});
                        };
                    };
                    if (info['upload-finished'] || info['upload-error']) {
                        if (info['upload-finished'] && !info['upload-error']) {
                            deferred.resolve(info);
                        } else {
                            error = info['upload-error'] || 'Unknow error';
                            deferred.reject({message: 'Upload failed ('+ error + ').'});
                        };
                    } else if (result.state() == "pending" && missing_retries) {
                        // Unless the file is completely uploaded or
                        // cancel request status again.
                        poll_retries = POLL_NETWORK_RETRIES;
                        poll_timeout = setTimeout(poll, POLL_NETWORK_DELAY);
                    };
                }, function() {
                    if (result.state() == "pending") {
                        if (poll_retries) {
                            poll_retries -= 1;
                            poll_timeout = setTimeout(poll, POLL_NETWORK_DELAY);
                        } else {
                            deferred.reject({message: 'Upload failed (Cannot check the status of the upload).'});
                        };
                    }
                });
            };
        return {
            promise: deferred.promise,
            start: function() {
                poll_timeout = setTimeout(poll, POLL_NETWORK_DELAY);
            },
            always: function() {
                if (poll_timeout !== null) {
                    clearTimeout(poll_timeout);
                    poll_timeout = null;
                };
            }
        };
    };

    var IFrameStatusChecker = function($iframe, name, result)  {
        // helper to bind an event on iframe load
        var iframe = $iframe.get(0),
            iframe_window = iframe.contentWindow,
            iframe_document = iframe_window.document,
            deferred = $.Deferred();

        var fail = function() {
            deferred.reject({message: 'Upload failed (File too big or server error).'});
        };

        $(document).one(name, function(event, data) {
            deferred.resolve(data);
        });
        if (iframe_window.addEventListener) {
            iframe_window.addEventListener("load", fail, false);
            iframe_window.addEventListener("error", fail, false);
        } else {
            iframe_window.attachEvent("onload", fail);
            iframe_window.attachEvent("onerror", fail);
        };
        return {
            promise: deferred.promise
        };
    };

    /**
     * UI compoments.
     */

    var UploadStatusMessage = function($display) {
        // Manage the status message of the upload widget.
        var $empty = $display.children('.upload-display-empty'),
            $uploading = $display.children('.upload-display-uploading'),
            $done = $display.children('.upload-display-complete');
        var empty = $empty.children('i').text(),
            uploading = jsontemplate.Template($uploading.children('i').text(), {}),
            done = jsontemplate.Template($done.children('i').text(), {}),
            state = 'empty',
            original = $display.data('upload-status');

        var api = {
            start: function(data) {
                if (state != 'starting') {
                    $uploading.children('i').text(uploading.expand(data));
                    $empty.hide();
                    $done.hide();
                    $uploading.show();
                    state = 'starting';
                }
            },
            progress: function(data) {
                if (state != 'uploading' && !data.missing) {
                    // Refresh information on the first notification of progress.
                    $uploading.children('i').text(uploading.expand(data));
                    state = 'uploading';
                };
            },
            done: function(data) {
                if (state != 'done') {
                    $done.children('i').text(done.expand(data));
                    $empty.hide();
                    $uploading.hide();
                    $done.show();
                    state = 'done';
                };
            },
            fail: function(data) {
                if (state != 'empty' || data.message) {
                    $empty.children('i').text(data.message || empty);
                    if (state != 'empty') {
                        $uploading.hide();
                        $done.hide();
                        $empty.show();
                        state = 'empty';
                    };
                };
            }
        };
        if (original) {
            api.done(original);
        };
        return api;
    };

    var UploadProgress = function($progress) {
        // Manage the progress bar of the upload widget.
        var progress = 0;

        return {
            start: function() {
                $progress.progressbar({value: 0}).show();
            },
            progress: function(data) {
                var updated = 0;

                if (!data['missing']) {
                    updated = data['uploaded-length'] * 100 / data['request-length'];
                };
                if (updated != progress) {
                    $progress.progressbar({value: updated});
                    progress = updated;
                };
            },
            always: function(data) {
                $progress.hide();
                progress = 0;
            }
        };
    };

    var UploadUI = function($field, set_objection, get_upload) {
        // Manage the controls of the upload widget (clear, cancel button).
        var $input = $field.children('.upload-input'),
            $cancel = $field.children('.upload-cancel'),
            $clear = $field.children('.upload-clear');
        var upload = null,
            objection = null,
            progress = UploadProgress($field.children('.upload-progress')),
            status = UploadStatusMessage($field.children('.upload-display')),
            api = {
                get: function(create) {
                    if (upload == null && create) {
                        upload = get_upload();
                        upload.register(status);
                        upload.register(progress);
                        upload.register(ui);
                    }
                    return upload;
                }
            },
            ui = {
                start: function() {
                    if (set_objection !== undefined) {
                        objection = $.Deferred();
                        set_objection(function () {
                            if (objection.state() == 'pending') {
                                var $dialog = $('<div title="Uploading file"><p>Please wait until the upload is finished ...</p><p class="progress"></p></div>'),
                                    $progress = $dialog.find('p.progress'),
                                    progress = 0;

                                $dialog.dialog({
                                    modal: true,
                                    closeOnEscape: false,
                                    resizable: false,
                                    draggable: false,
                                    beforeClose: function() {
                                        return false;
                                }});
                                $progress.progressbar({value: 0});
                                api.get().register({
                                    progress: function(data) {
                                        var updated = 0;

                                        if (!data['missing']) {
                                            updated = data['uploaded-length'] * 100 / data['request-length'];
                                        };
                                        if (updated != progress) {
                                            $progress.progressbar({value: updated});
                                            progress = updated;
                                        };
                                    }
                                });
                                return objection.always(function() {
                                    $dialog.dialog('close').remove();
                                    objection = null;
                                });
                            };
                            return null;
                        });
                    };
                    $cancel.show();
                },
                done: function(data) {
                    $input.attr('value', $field.data('upload-identifier'));
                },
                always: function(data) {
                    if (objection !== null) {
                        objection.resolve();
                    };
                    $cancel.hide();
                    upload = null;
                }
            };

        $cancel.on('click', function() {
            var upload = api.get();
            if (upload !== null) {
                upload.cancel();
            };
        });
        $clear.on('click', function() {
            var upload = api.get(true);
            upload.cancel();
            $input.attr('value', '');
        });
        return api;
    };

    /**
     * Implementations for the uploading (with and without popup).
     */

    var UploadForm = function($field, identifier, url) {
        // Upload a file input using the given identifier at the given URL.
        // It will trigger callbacks uring various steps of the progress.
        var $upload = $('<div style="display:none">' +
                        '<iframe width="0" height="0" style="display:none"' +
                        'src="about:blank" class="upload-iframe" name="upload-' +
                        identifier + '-iframe"></iframe>' +
                        '<form class="upload-form" enctype="multipart/form-data"' +
                        'method="POST" action="' + url + '?identifier=' + identifier +
                        '" target="upload-' + identifier +
                        '-iframe" id="upload-' + identifier + '-form">' +
                        '<input type="reset" class="upload-reset" /></form></div>'),
            result = $.Deferred().fail(function() {
                $upload.find('.upload-reset').click();
                $upload.find('.upload-iframe').attr('src', 'javascript:false;');
            }).always(function() {
                $upload.remove();
                $field.removeAttr('form');
            }),
            start = $.Deferred(),
            api = {
                start: function() {
                    $.ajax({
                        type: 'GET',
                        dataType: 'json',
                        url: url + '?clear&identifier=' + identifier}).then(function () {
                            $('body').append($upload);
                            $field.attr('form', 'upload-' + identifier + '-form');
                            start.done(function() {
                                api.register(IFrameStatusChecker($upload.find('iframe'), 'upload-' + identifier + '-done'));
                                api.register(PollStatusChecker(url, identifier, result));
                                $upload.find('form').submit();
                            }).resolve({
                                'uploaded-length': 0, 'content-type': 'n/a', 'request-length': 0, 'filename': ''});
                        }, function() {
                            result.reject({message: 'Upload failed.'});
                        });
                },
                cancel: function() {
                    result.reject({});
                },
                register: function(plugin) {
                    if (plugin.start !== undefined) {
                        start.done(plugin.start);
                    };
                    if (plugin.promise !== undefined) {
                        plugin.promise().then(function(data) {
                            result.resolve(data);
                        }, function(data) {
                            result.reject(data);
                        });
                    };
                    for (var event in {progress: 1, done: 1, fail: 1, always: 1}) {
                        if (plugin[event] !== undefined) {
                            result[event](plugin[event]);
                        };
                    };
                    return api;
                }
            };
        return api;
    };

    var UploadPopup = function(identifier, url) {
        // Upload a file input using the given identifier at the given URL.
        // It will trigger callbacks uring various steps of the progress.
        var $popup = $('<div  title="Upload a file">' +
                       '<form class="upload-form" enctype="multipart/form-data"' +
                       'method="POST" action="' + url + '?identifier=' + identifier +
                        '" target="upload-' + identifier +
                       '-iframe" id="upload-' + identifier + '-form">' +
                       '<input type="file" name="file-we-are-uploading" class="upload-file" /></form>'+
                       '<iframe width="0" height="0" style="display:none"' +
                       'src="about:blank" class="upload-iframe" name="upload-' +
                       identifier + '-iframe"></iframe></div>'),
            result = $.Deferred().fail(function() {
                $popup.find('.upload-iframe').attr('src', 'javascript:false;');
            }).always(function() {
                $popup.remove();
            }),
            start = $.Deferred(),
            api = {
                start: function() {
                    var send = function() {
                        $.ajax({
                            type: 'GET',
                            dataType: 'json',
                            url: url + '?clear&identifier=' + identifier}).then(function() {
                                start.done(function() {
                                    $popup.dialog('close');
                                    api.register(IFrameStatusChecker($popup.find('iframe'), 'upload-' + identifier + '-done'));
                                    api.register(PollStatusChecker(url, identifier, result));
                                    $popup.find('form').submit();
                                }).resolve({
                                    'uploaded-length': 0, 'content-type': 'n/a', 'request-length': 0, 'filename': ''});
                            }, function() {
                                result.reject({message: 'Upload failed.'});
                            });
                    };
                    $popup.find('.upload-file').on('change', function() {
                        send();
                    });
                    $popup.dialog({
                        buttons: {
                            Send: function() {
                                send();
                            }
                        }
                    });
                },
                cancel: function() {
                    result.reject({});
                },
                register: function(plugin) {
                    if (plugin.start !== undefined) {
                        start.done(plugin.start);
                    };
                    if (plugin.promise !== undefined) {
                        plugin.promise().then(function(data) {
                            result.resolve(data);
                        }, function(data) {
                            result.reject(data);
                        });
                    };
                    for (var event in {progress: 1, done: 1, fail: 1, always: 1}) {
                        if (plugin[event] !== undefined) {
                            result[event](plugin[event]);
                        };
                    };
                    return api;
                }
            };
        return api;
    };

    var UploadField = DONT_NEED_POPUP ?
            function ($field, set_objection) {
        var $trigger = $field.children('.upload-trigger'),
            $file = $field.children('.upload-file-input'),
            ui = UploadUI($field, set_objection, function() {
                return UploadForm($file, $field.data('upload-identifier'), $field.data('upload-url')).register({
                    start: function() {
                        $file.hide();
                    },
                    always: function() {
                        $file.show();
                    }
                });
            });

        $trigger.remove();
        $file.on('change', function() {
            ui.get(true).start();
        });
    } : function($field, set_objection) {
        var $trigger = $field.children('.upload-trigger'),
            $file = $field.children('.upload-file-input'),
            ui = UploadUI($field, set_objection, function() {
                return UploadPopup($field.data('upload-identifier'), $field.data('upload-url')).register({
                    start: function() {
                        $trigger.hide();
                    },
                    always: function() {
                        $trigger.show();
                    }
                });
            });

        $file.detach();
        $trigger.show();
        $trigger.on('click', function(){
            ui.get(true).start();
        });
    };

    $(document).on('loadwidget-smiform', '.form-fields-container', function(event, data) {
        $(this).find('.upload-file').each(function(){
            UploadField($(this), data.set_objection);
        });
        event.stopPropagation();
    });

})(jQuery, jsontemplate);
