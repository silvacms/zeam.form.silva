
(function(infrae, $) {

    var create_cropping_field = function() {
        var $field = $(this);
        var $input = $field.find('input.field-cropcoordinates');
        var $opener = $field.find('a.widget-crop-popup-button');
        var $template = $field.find('div.widget-crop-popup');
        var required = $input.hasClass('field-required');

        $opener.bind('click', function(event){
            var $popup = $template.clone();
            var $img = $popup.find('img.widget-crop-image');

            var image_width = $img.get(0).width;
            var image_height = $img.get(0).height;
            var original_width = Math.max(40 + image_width, 250);
            var original_height = 145 + image_height;

            var $proportional = $popup.find('input.crop-proportional');

            var crop = undefined;  //Crop coordinates
            if ($input.val()) {
                crop = $input.val().replace(
                        /^\s*(\d+)x(\d+)-(\d+)x(\d+)\s*$/,
                    '$1,$2,$3,$4').split(',');
            };

            var need_refresh = false; //Resize need a last refresh with box 0
            var jCrop = undefined; //API to change keep ratio and resize

            var create_cropping = function(options) {
                // Create or recreate the cropping with new options
                var current;

                options = $.extend(options, {
                    onSelect: function(value){
                        crop = [value.x, value.y, value.x2, value.y2];
                    }
                });
                if (jCrop !== undefined) {
                    jCrop.destroy();
                };
                if (crop !== undefined) {
                    options['setSelect'] = crop;
                };
                jCrop = $.Jcrop($img, options);
            };

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
                        $input.val(crop[0] + 'x' +
                                   crop[1] + '-' +
                                   crop[2] + 'x' +
                                   crop[3]);
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
                        jCrop.setOptions({aspectRatio: image_width / image_height});
                    } else {
                        jCrop.setOptions({aspectRatio: 0});
                    };
                };
            });
            // Cleanup everything when the popup is closed
            $popup.bind('dialogclose', function() {
                $popup.remove();
            });
            $popup.bind('infrae-ui-dialog-resized', function (event, popup_size) {
                var candidate_width = popup_size.width - 40;
                var candidate_height = popup_size.height - 145;

                if ((candidate_width < image_width) ||
                    (candidate_height < image_height)) {
                    var ratio = Math.min(
                        candidate_width/image_width,
                        candidate_height/image_height);
                    create_cropping({boxWidth: ratio * image_width,
                                     boxHeight: ratio * image_height});
                    need_refresh = true;
                } else {
                    if (need_refresh) {
                        create_cropping();
                        need_refresh = false;
                    };
                };
            });
            $popup.dialog({
                autoOpen: false,
                modal: true,
                minWidth: 250,
                width: original_width,
                height: original_height,
                open: create_cropping,
                buttons: actions
            });
            infrae.ui.ShowDialog($popup, {factor:0.9});
        });
    };

    $('form').live('load-smiform', function() {
        $(this).find('div.widget-crop').each(create_cropping_field);
    });

    $(document).ready(function(){
        $('div.widget-crop').each(create_cropping_field);
    });

})(infrae, jQuery);
