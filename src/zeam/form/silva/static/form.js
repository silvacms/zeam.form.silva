// ZEAM JS support scripts

var RemoteZeamForm = function(popup, url) {
    this.popup = popup;
    this.url = url;
};

RemoteZeamForm.prototype.update = function (data) {
    var form = $('<form></form>');
    var buttons = {}
    var self = this;

    this.popup.dialog('option', 'title', data['label']);
    this.popup.empty();
    this.popup.append(form);
    form.append(data['widgets']);
    form.children('.field-required:first').trigger('focus');
    for (var i=0; i < data['actions'].length; i++) {
        var action_label = data['actions'][i]['label'];
        var action_name = data['actions'][i]['name'];
        buttons[action_label] = function() {
            var form_array = form.serializeArray();
            var form_data = {};
            form_data[action_name] = action_label;
            for (var j=0; j < form_array.length; j++) {
                form_data[form_array[j]['name']] = form_array[j]['value'];
            };
            $.getJSON(self.url, form_data, function(data) {
                self.update(data);
            });
        };
    };
    buttons['cancel'] = function() {
        $(this).dialog('close');
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
            height: 400,
            width: 800,
        });
        var form = new RemoteZeamForm(popup, url);
        form.display()
        return false;
    });
});
