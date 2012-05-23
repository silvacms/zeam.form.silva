
(function($, infrae) {

    var create_multipickup_field = function() {
        var $field = $(this);
        $field.multiselect({sortable: false, doubleClickable: false});
    };

    $('.form-fields-container').live('loadwidget-smiform', function(event) {
        $(this).find('.field-multipickup').each(create_multipickup_field);
        event.stopPropagation();
    });

    $(document).ready(function() {
        $('.field-multipickup').each(create_multipickup_field);
    });

})(jQuery, infrae);
