// ZEAM JS support scripts


var zeam_focus_field = function(form) {
    // Focus error field first
    field = form.find('.field-error:first').find('.field:first');
    if (field.length) {
        field.trigger('focus');
    }
    else {
        // Focus first required field otherwise
        form.find('.field-required:first').trigger('focus');
    };
};


var InlineZeamValidator = function(input) {
    this.input = input;
    this.name = input.attr('name');
    this.value = input.attr('value');
};


InlineZeamValidator.prototype.available = function () {
    // Says if the functionality is available or not. We only do it on
    // what we know we can serialize.
    var input_type = this.input.attr('type');
    if (input_type == 'text' || input_type == 'url' ||
        input_type == 'email' || input_type == 'tel' ||
        input_type == 'number') {
        return true;
    };
    return false;
};

InlineZeamValidator.prototype.validate = function () {
    if (!this.available()) {
        return false;
    }
    var self = this;
    var info = {};
    var form_url = this.input.closest('form').attr('action');
    info['name'] = this.name;
    info['value'] = this.value;
    $.ajax({
        url: form_url + '/++rest++form-validate',
        type: 'POST',
        dataType: 'json',
        data: info,
        success: function(data) {
            if (data['success']) {
                self.clearError();
            }
            else {
                self.setError(data['error']);
            };
        }});
};

InlineZeamValidator.prototype.setError = function (error_text) {
    var cell = this.input.parent();
    var error = cell.find('.error');
    if (!error.length) {
        error = $('<div class="error"></div>');
        cell.prepend(error);
    };
    error.text(error_text);
};

InlineZeamValidator.prototype.clearError = function() {
    var cell = this.input.parent();
    var error = cell.find('.error');
    if (error) {
        error.remove();
    };
};


var PopupZeamForm = function(popup, url) {
    this.popup = popup;
    this.url = url;
};

PopupZeamForm.prototype._postForm = function(form_data, callback) {
    $.ajax({
        url: this.url,
        type: 'POST',
        dataType: 'json',
        data: form_data,
        success: callback
    });
};

PopupZeamForm.prototype._refresh = function(identifier) {
    var self = this;
    $.getJSON(
        document.location + '/++rest++form-refresh',
        {'identifier': identifier},
        function (data) {
            $('#' + identifier).replaceWith(data['form']);
            self.close();
        });
};

PopupZeamForm.prototype._buildButtonCallback = function(form, data) {
    var self = this;
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
            self._postForm(form_data,  function(data) {
                if (action_type == 'close_on_success' && data['success']) {
                    if (data['refresh']) {
                        self._refresh(data['refresh']);
                    }
                    else {
                        self.close();
                    };
                }
                else {
                    self.update(data);
                    self.focus();
                };
            });
        };
        if (action_type == 'close') {
            self.close();
        };
        return false;
    };
};

PopupZeamForm.prototype.close = function() {
    this.popup.dialog('close');
    this.popup.empty();
    $(document).trigger('zeam-popup-closed');
};

PopupZeamForm.prototype.update = function(data) {
    var form = $('<form method="post" enctype="multipart/form-data" />');
    var buttons = {}

    this.popup.dialog('option', 'title', data['label']);
    this.popup.empty();
    this.popup.append(form);
    form.attr('action', this.url);
    form.append(data['widgets']);
    // Add an empty input submit to activate form submission with enter
    form.append($('<input type="submit" style="display: none" />'));
    for (var i=0; i < data['actions'].length; i++) {
        var label = data['actions'][i]['label'];
        var callback = this._buildButtonCallback(form, data['actions'][i]);
        buttons[label] = callback;
        if (data['actions'][i]['name'] == data['default_action']) {
            form.bind('submit', callback);
        };
    };
    this.popup.dialog('option', 'buttons', buttons);
};

PopupZeamForm.prototype.focus = function() {
    zeam_focus_field(this.popup);
};

PopupZeamForm.prototype.display = function() {
    var self = this;
    $.getJSON(this.url, function(data) {
        self.update(data);
        self.popup.dialog('open');
        self.focus();
    });
};

$(document).ready(function() {
    // Focus form field
    zeam_focus_field($('.zeam-form'));
    // Inline validation
    $('.zeam-inline-validation').find('.field').live('change', function() {
        var validator = new InlineZeamValidator($(this));
        validator.validate();
        return true;
    });
    // Select all
    $('.zeam-form').find('.zeam-select-all').live('change', function() {
        var select = $(this);
        var status = select.attr('checked');
        $('.zeam-form').find('.' + select.attr('name')).each(function() {
            $(this).attr('checked', status);
        });
    });
    // Prepare REST forms
    $('.link-popup-form').live('click', function() {
        var url = $(this).attr('href');
        var popup = $('#remote-form-dialog');
        popup.dialog({
            autoOpen: false,
            modal: true,
            width: 800
        });
        var form = new PopupZeamForm(popup, url);
        form.display();
        return false;
    });
});
