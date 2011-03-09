
(function($) {

    var create_cropping_field = function(field) {
        var button = field.find('a.widget-crop-popup-button');
        var popup = field.find('div.widget-crop-popup');
        var img = popup.find('img.widget-crop-image');

        popup.dialog({
            modal: true,
            autoOpen: false,
            buttons: {
                Ok: function(){
                    var c = img.data('crop');
                    if (c !== undefined) {
                        $('input', field).val(
                            c.x + 'x' + c.y + '-' + c.x2 + 'x' + c.y2);
                        popup.dialog('close');
                    }
                },
                Cancel: function(){ popup.dialog('close'); }
            }
        });

        button.bind('click', function(event){
            img.Jcrop({
                onSelect: function(c){
                    img.data('crop', c);
                },
                onChange: function(c){
                    img.data('crop', c);
                }
            });
            popup.dialog('open');
        });
    };

    $('form').live('load-smiform', function() {
        $(this).find('div.widget-crop').each(function(index, field){
            create_cropping_field($(field));
        });
    });

    $(document).ready(function(){
        $('div.widget-crop').each(function(index, field) {
            create_cropping_field($(field));
        });
    });

})(jQuery);
