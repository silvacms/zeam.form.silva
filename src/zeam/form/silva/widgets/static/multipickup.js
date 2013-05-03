
(function($, infrae) {

    var create_multipickup_field = function() {
        var $field = $(this);
        $field.multiselect({sortable: false});
    };

    $(document).on('loadwidget-smiform', '.form-fields-container', function(event) {
        $(this).find('.field-multipickup').each(create_multipickup_field);
        event.stopPropagation();
    });

})(jQuery, infrae);
