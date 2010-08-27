// ZEAM JS support scripts


var focus_zeam_field = function(form) {
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

var PopupZeamForm = function(popup, url) {
    this.popup = popup;
    this.url = url;
};

PopupZeamForm.prototype._postForm = function (form_data, callback) {
    $.ajax({
        url: self.url,
        type: 'POST',
        dataType: 'json',
        data: form_data,
        success: callback,
    });
};

PopupZeamForm.prototype._buildButton = function (form, data) {
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
                    self.close();
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
    };
};

PopupZeamForm.prototype.close = function () {
    self.popup.dialog('close');
    self.popup.empty();
};

PopupZeamForm.prototype.update = function (data) {
    var form = $('<form></form>');
    var buttons = {}

    this.popup.dialog('option', 'title', data['label']);
    this.popup.empty();
    this.popup.append(form);
    form.append(data['widgets']);
    for (var i=0; i < data['actions'].length; i++) {
        var label = data['actions'][i]['label'];
        buttons[label] = this._buildButton(form, data['actions'][i]);
    };
    this.popup.dialog('option', 'buttons', buttons);
};

PopupZeamForm.prototype.focus = function() {
    focus_zeam_field(this.popup);
};

PopupZeamForm.prototype.display = function() {
    self = this;
    $.getJSON(self.url, function(data) {
        self.update(data);
        self.popup.dialog('open');
        self.focus();
    });
};

$(document).ready(function() {
    // Focus form field
    focus_zeam_field($('.zeam-form'));
    // Prepare REST forms
    $('.link-popup-form').bind('click', function() {
        var url = $(this).attr('href');
        var popup = $('#remote-form-dialog');
        popup.dialog({
            autoOpen: false,
            modal: true,
            width: 800,
        });
        var form = new PopupZeamForm(popup, url);
        form.display()
        return false;
    });
});
