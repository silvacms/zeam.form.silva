
(function($) {

    var create_cropping_field = function(field) {
        var button = field.find('a.widget-crop-popup-button');
        var popup = field.find('div.widget-crop-popup');
        var img = popup.find('img.widget-crop-image');
        var cbx = field.find('input.crop-proportional');

        var width = $(window).width();
        var height = $(window).height();

        var imageWidth = width - width * 0.2;
        var imageHeight = height - height * 0.3;

        var popupWidth = width - width * 0.1;
        var popupHeight = height - height * 0.1;

        var api = null;

        cbx.change(function(){
            if (api !== null) {
                if (!!this.checked) {
                    api.setOptions({aspectRatio: img.width() / img.height()});
                } else {
                    api.setOptions({aspectRatio: 0});
                }
            }
        });

        popup.dialog({
            modal: true,
            autoOpen: false,
            width: popupWidth,
            height: popupHeight,
            open: function() {
                if (api === null) {
                    api = $.Jcrop(img, {
                        boxWidth: imageWidth,
                        boxHeight: imageHeight,
                        onSelect: function(c){
                            img.data('crop', c);
                        },
                        onChange: function(c){
                            img.data('crop', c);
                        }
                    });
                }
                var value = $('input', field).val();
                var select = value.replace(
                        /^\s*(\d+)x(\d+)-(\d+)x(\d+)\s*$/,
                        '$1,$2,$3,$4').split(',');
                api.setSelect(select);
            },
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
