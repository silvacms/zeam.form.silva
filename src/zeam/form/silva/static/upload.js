var Uploader = function(element, options){
    var defaults = {
        statTimeout: 5000,
        statDelay: 500
    };

    this.progress = 0;
    this.retries = 0;
    this.options = $.extend(defaults, options);
    this.element = $(element);
    this.uploadId = Math.random() * 10000000000000000000;
    this.statURL = '/gp.fileupload.stat/';
    this._timeout = null;
};


$.extend(Uploader.prototype, {

    createForm: function(target, action) {
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
    },

    getStatus: function(delay) {
        this._clearTimeout();
        this._timeout = setTimeout(
            this._getStatusCallback.scope(this), this.options.statDelay);
    },

    terminate: function() {
        this.progress = 100;
        this.element.trigger('upload.complete', this.uploadId);
    },

    finalize: function(filename) {
        this.element.trigger('finished.upload', filename);
    },

    stop: function(message) {
        this._clearTimeout();
        this.progress = 100;
        this.element.trigger('failure.upload', message);
    },

    _clearTimeout: function() {
        if (this._timeout !== null) {
            clearTimeout(this._timeout);
            this._timeout = null;
        }
    },

    _setProgress: function(value) {
        var old = this.progress;
        if (value != old) {
            this.progress = value;
            this.element.trigger('finished.upload', value);
        }
    },

    _getStatusCallback: function() {
        var query = '?q=' + (Math.random() * 10000000000000000000);
        $.ajax({
            type: 'GET',
            dataType: 'json',
            timeout: this.options.statTimeout,
            url: this.statURL + this.uploadId + query,
            success: function(data) {
                    if (data.state == -1) {
                        this.stop(this.options.tooManyTriesLabel);
                        return;
                    }
                    if (data.state == 0) {
                        // not started
                        this.retries += 1;
                        if (this.retries > this.max_retries) {
                            this.stop();
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
                     this.stop();
                 } else {
                    this.getStatus(this.options.statDelay);
                 }
             }.scope(this)
        });
    },

    start: function() {
        // listen to event triggered by the iframe
        $(document).one('upload-finished', function(event, data){
            this.finalize(data['paths'][0]);
        }.scope(this));
        this._form.submit();
        this.getStatus();
    }
});

$(document).ready(function() {

  $.each($('.upload-file', $(document.body)), function(index, el){
      var element = $(el);
      var iframe = $('iframe', element);
      var progress = $('.upload-progress', element);
      var trigger = $('a.upload-trigger', element);
      var input = $('.upload-input', element);
      var display = $('.upload-display', element);
      var oldValue = input.val();
      var popup = $('.upload-popup', element);
      var uploader = new Uploader(element);

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
      element.bind('progress.upload', function(event, value){
          progress.progressbar('option', 'value', value);
      });
      element.bind('finished.upload', function(event, filename){
          input.val(filename);
          progress.hide();
          display.text(filename.replace(/^.*[\/\\](.*)/, '$1'));
          trigger.button('enable');
          trigger.show();
      });
      element.bind('failure.upload', function(event, message){
          input.val(oldValue);
          display.text(oldValue.replace(/^.*[\/\\](.*)/, '$1'));
          progress.hide();
          trigger.button('enable');
          trigger.show();
      });
  });

});
