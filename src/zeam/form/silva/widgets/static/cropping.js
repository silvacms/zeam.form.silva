
(function($) {

    $(document).ready(function(){
        $('div.widget-crop').each(function(index) {
            var widget = $(this);
            var button = $('a.widget-crop-popup-button', widget);
            var popup = $('div.widget-crop-popup', widget);
            var img = $('img.widget-crop-image', popup);

            popup.dialog({
                modal: true,
                autoOpen: false,
                buttons: {
                    Ok: function(){
                        var c = img.data('crop');
                        if (c !== undefined) {
                            $('input', widget).val(
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
        });
    });

})(jQuery);
