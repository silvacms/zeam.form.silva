

(function($) {

    var create_cropping_field = function() {
        var $field = $(this);
        var $input = $field.find('input');
        var $opener = $field.find('a.widget-crop-popup-button');
        var $template = $field.find('div.widget-crop-popup');
        var required = $input.hasClass('field-required');

        var width = $(window).width();
        var height = $(window).height();

        var imageWidth = 0.8 * width;
        var imageHeight = 0.7 * height;

        var popupWidth = 0.9 * width;
        var popupHeight = 0.9 * height;

        $opener.bind('click', function(event){
            var $popup = $template.clone();
            var $img = $popup.find('img.widget-crop-image');
            var $proportional = $popup.find('input.crop-proportional');
            var crop = undefined;
            var jCrop = undefined;

            // Define popup actions
            var actions = {
                Cancel: function() {
                    $popup.dialog('close');
                },
                Clear: function() {
                    $input.val('');
                    $popup.dialog('close');
                },
                Ok: function(){
                    if (crop !== undefined) {
                        $input.val(
                            crop.x + 'x' + crop.y + '-' + crop.x2 + 'x' + crop.y2);
                        $popup.dialog('close');
                    }
                }
            };
            if (required) {
                delete actions['Clear'];
            };

            // Bind proportional option
            $proportional.change(function(){
                if (jCrop !== null) {
                    if (!!this.checked) {
                        jCrop.setOptions({aspectRatio: $img.width() / $img.height()});
                    } else {
                        jCrop.setOptions({aspectRatio: 0});
                    };
                };
            });

            // Cleanup everything when the popup is closed
            $popup.bind('dialogclose', function() {
                $popup.remove();
            });
            $popup.dialog({
                modal: true,
                autoOpen: true,
                width: popupWidth,
                height: popupHeight,
                open: function() {
                    jCrop = $.Jcrop($img, {
                        boxWidth: imageWidth,
                        boxHeight: imageHeight,
                        onSelect: function(value){
                            crop = value;
                        },
                        onChange: function(value){
                            crop = value;
                        }
                    });
                    var select = $input.val().replace(
                            /^\s*(\d+)x(\d+)-(\d+)x(\d+)\s*$/,
                        '$1,$2,$3,$4').split(',');
                    jCrop.setSelect(select);
                },
                buttons: actions
            });
        });
    };

    $('form').live('load-smiform', function() {
        $(this).find('div.widget-crop').each(create_cropping_field);
    });

    $(document).ready(function(){
        $('div.widget-crop').each(create_cropping_field);
    });

})(jQuery);
