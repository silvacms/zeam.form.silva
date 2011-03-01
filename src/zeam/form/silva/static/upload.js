
(function($) {

    function basename(path) {
        return path.replace(/^.*[\/\\](.*)/, '$1');
    }

    var FileUploader = function(element, options){
        var defaults = {
            statTimeout: 5000,
            statDelay: 500,
            tooManyTriesLabel: 'unknown error while uploading file.',
            fileTooBigLabel: 'upload failed file is too big.'
        };
        this.progress = 0;
        this.retries = 0;
        this.options = $.extend(defaults, options);
        this.element = $(element);
        this.uploadId = Math.random() * 10000000000000000000;
        this.statURL = '/gp.fileupload.stat/';
        this._timeout = null;
    };

    FileUploader.prototype.createForm = function(target, action) {
        var form = $('<form class="upload-form"' +
                     'enctype="multipart/form-data"' +
                     'method="POST"' +
                     'action=""' +
                     'target="">' +
                     '<input type="file" name="file" />' +
                     '</form>');
        form.attr('target', target);
        var sep = '?';
        if (action.match(/\?/))
            sep = "&";
        form.attr('action', action + sep + 'gp.fileupload.id=' + this.uploadId);
        this._form = form;
        return form;
    };

    FileUploader.prototype.getStatus = function(delay) {
        this._clearTimeout();
        this._timeout = setTimeout(
            this._getStatusCallback.scope(this), this.options.statDelay);
    };

    FileUploader.prototype.terminate = function() {
        this.progress = 100;
        this.element.trigger('complete-fileupload', this.uploadId);
    };

    FileUploader.prototype.finalize = function(filename) {
        this.element.trigger('finished-fileupload', filename);
    };

    FileUploader.prototype.stop = function(message) {
        this._clearTimeout();
        this.progress = 100;
        this.element.trigger('failure-fileupload', message);
    };

    FileUploader.prototype._clearTimeout = function() {
        if (this._timeout !== null) {
            clearTimeout(this._timeout);
            this._timeout = null;
        }
    };

    FileUploader.prototype._setProgress = function(value) {
        var old = this.progress;
        if (value != old) {
            this.progress = value;
            this.element.trigger('progress-fileupload', value);
        }
    };

    FileUploader.prototype._getStatusCallback = function() {
        var query = '?q=' + (Math.random() * 10000000000000000000);
        $.ajax({
            type: 'GET',
            dataType: 'json',
            timeout: this.options.statTimeout,
            url: this.statURL + this.uploadId + query,
            success: function(data) {
                if (data.state == -1) {
                    this.stop(this.options.fileTooBigLabel);
                    return;
                }
                if (data.state == 0) {
                    // not started
                    this.retries += 1;
                    if (this.retries > this.max_retries) {
                        this.stop(this.options.tooManyTriesLabel);
                    } else {
                        this.getStatus();
                    }
                    return;
                } else {
                    this.retries = 0;
                }
                if (data.percent >= 0 && data.percent < 100) {
                    // progress
                    this._setProgress(data.percent);
                    this.getStatus();
                }
                if (data.percent == 100) {
                    this._setProgress(data.percent);
                    this.terminate();
                }
            }.scope(this),
            error: function() {
                this.retries += 1;
                if (this.retries > 3) {
                    this.stop(this.options.tooManyTriesLabel);
                } else {
                    this.getStatus(this.options.statDelay);
                }
            }.scope(this)
        });
    };

    FileUploader.prototype.start = function() {
        // listen to event triggered by the iframe
        $(document).one('done-' + String(this.uploadId) + '-upload',
            function(event, data){
                this.finalize(data.path);
            }.scope(this));
        this._form.submit();
        this.getStatus();
    };

    var create_upload_field = function(field) {

        var iframe = $('iframe', field);
        var progress = $('.upload-progress', field);
        var trigger = $('a.upload-trigger', field);
        var input = $('.upload-input', field);
        var display = $('.upload-display', field);
        var oldValue = input.val();
        var popup = $('.upload-popup', field);
        var uploader = new FileUploader(field);

        popup.dialog({
            title: trigger.text(),
            modal: true,
            create: function(){
                $('p', $(this)).append(
                    uploader.createForm(
                        iframe.attr('name'), trigger.attr('href')));
            },
            autoOpen: false,
            buttons: {
                'send': function(event){
                    $(this).dialog('close');
                    $(event.target).closest('ui-button-text').button('disable');
                    uploader.start();
                    progress.show();
                    trigger.button('disable');
                    trigger.hide();
                }
            }
        });

        trigger.button({'icons': {'primary': 'ui-icon-document'}});
        trigger.bind('click', function(){ popup.dialog('open'); });
        progress.progressbar({value: 0});
        field.bind('progress-fileupload', function(event, value){
            progress.progressbar('option', 'value', value);
        });
        field.bind('finished-fileupload', function(event, filename){
            input.val(filename);
            progress.hide();
            display.text(basename(filename));
            trigger.button('enable');
            trigger.show();
        });
        field.bind('failure-fileupload', function(event, message){
            field.trigger('notify', {'message': message,
                'category': 'error'});
            input.val(oldValue);
            display.text(basename(oldValue));
            progress.hide();
            trigger.button('enable');
            trigger.show();
        });
    };

    $('form').live('load-smiform', function() {
        $(this).find('.upload-file').each(function(index, field){
            create_upload_field($(field));
        });
    });

    $(document).ready(function() {
        $('.upload-file').each(function(index, field){
            create_upload_field($(field));
        });
    });


})(jQuery);
