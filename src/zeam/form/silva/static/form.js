// ZEAM JS support scripts

var RemoteZeamForm = function(popup, url) {
    this.popup = popup;
    this.url = url;
};

RemoteZeamForm.prototype._buildButton = function (form, data) {
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
            $.getJSON(self.url, form_data, function(data) {
                if (action_type == 'close_on_success' && data['success']) {
                    self.popup.dialog('close');
                }
                else {
                    self.update(data);
                };
            });
        };
        if (action_type == 'close') {
            self.popup.dialog('close');
        };
    };
};

RemoteZeamForm.prototype.update = function (data) {
    var form = $('<form></form>');
    var buttons = {}

    this.popup.dialog('option', 'title', data['label']);
    this.popup.empty();
    this.popup.append(form);
    form.append(data['widgets']);
    form.children('.field-required:first').trigger('focus');
    for (var i=0; i < data['actions'].length; i++) {
        var label = data['actions'][i]['label'];
        buttons[label] = this._buildButton(form, data['actions'][i]);
    };
    this.popup.dialog('option', 'buttons', buttons);
};

RemoteZeamForm.prototype.display = function() {
    self = this;
    $.getJSON(self.url, function(data) {
        self.update(data);
        self.popup.dialog('open');
    });
};

$(document).ready(function() {
    // Focus first required field
    $('.zeam-form .field-required:first').trigger('focus');
    // Prepare REST forms
    $('.link-remote-form').bind('click', function() {
        var url = $(this).attr('href');
        var popup = $('#remote-form-dialog');
        popup.dialog({
            autoOpen: false,
            modal: true,
            width: 800,
        });
        var form = new RemoteZeamForm(popup, url);
        form.display()
        return false;
    });
});
