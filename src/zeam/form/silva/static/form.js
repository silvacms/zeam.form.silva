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
    this.input = $(input);
    this.name = this.input.attr('name');
    this.value = this.input.attr('value');
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

InlineZeamValidator.prototype.initialize = function () {
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
    $(document).trigger('smi-refresh-feedback');
};

PopupZeamForm.prototype.update = function(data) {
    var form = $('<form method="post" enctype="multipart/form-data" ' +
                 'class="zeam-form zeam-inline-validation" />');
    var buttons = {};

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
    form.trigger('zeam-form-ready');
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


var ZeamDateField = function(field) {
    this.field = $(field);
    var id = this.field.attr('id');
    this.year = $('#' + id + '-year');
    this.month = $('#' + id + '-month');
    this.day = $('#' + id + '-day');
    this.hour = $('#' + id + '-hour');
    this.min = $('#' + id + '-min');
    this.lang = $(document).find('html').attr('lang');
};

ZeamDateField.prototype.initialize = function () {
    var number_reg = /^(\d)+$/;
    var self = this;
    var settings = {};
    var lang_settings = $.datepicker.regional[this.lang];
    if (!lang_settings) {
        lang_settings = $.datepicker.regional[''];
    };
    for (key in lang_settings) {
        settings[key] = lang_settings[key];
    };
    settings['showOn'] = 'button';
    settings['buttonImage'] = '/++resource++silva.core.smi/calendar.gif';
    settings['showWeek'] = true;
    settings['showOtherMonths'] = true;
    settings['dateFormat'] = 'yy/mm/dd';
    settings['onSelect'] = function(date, picker) {
        var parts = date.split('/');
        self.day.val(parts[2]);
        self.month.val(parts[1]);
        self.year.val(parts[0]);
        if (!self.hour.val()) {
            self.hour.val('00');
        };
        if (!self.min.val()) {
            self.min.val('00');
        };
    };
    settings['beforeShow'] = function() {
        var day = self.day.val();
        var month = self.month.val();
        var year = self.year.val();
        if (day && month && year) {
            self.field.datepicker(
                'setDate', new Date(year, month - 1, day));
        };
    };
    this.field.datepicker(settings);
};


$('form').live('zeam-form-ready', function () {
    var form = $(this);

    // Focus form field
    zeam_focus_field(form);
    // Inline validation
    if (form.hasClass('zeam-inline-validation')) {
        form.find('.field').bind('change', function() {
            var validator = new InlineZeamValidator(this);
            validator.initialize();
            return true;
        });
    };
    // Datetime fields on the page
    form.find('.field-datetime').each(function(index) {
        var field = new ZeamDateField($(this));
        field.initialize();
    });
    // Select all
    form.find('.zeam-select-all').bind('change', function() {
        var select = $(this);
        var status = select.attr('checked');
        form.find('.' + select.attr('name')).each(function() {
            $(this).attr('checked', status);
        });
    });
});

$(document).ready(function() {
    // Send form init event
    $('.zeam-form').trigger('zeam-form-ready');

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
