$(document).ready(function() {

  $('a.open-upload-popup').live('click', function(){
      var popup = $('<div.upload-popup style="display:none" />');
      popup.appendTo(document.body);

      var popupButtons = {};

      popup.dialog({
          autoOpen: false,
          modal: true,
          height: 500,
          width: 600,
          zIndex: 12001,
          buttons: popupButtons
      });

      var action = $('a#content-url').attr('href') + '/++rest++upload/';
      var uploadForm = $('<form enctype="multipart/form-data'+
                            'method="POST"' +
                            'action="." >' +
                            '<input type="file" name="file" />' +
                         '</form>');
      uploadForm.appendTo(popup);

      $(document).one('upload-finished', function(event, data){
          var path = data['paths'][0];
          var filename = path.replace(/^.*\/(.*)$/, '$1');
          $(this).siblings('input:hidden').first().val(path);
          $(this).siblings('span.display-value').first().text(filename);
          popup.dialog('destroy');
      }.scope(this));

      popup.fileUpload({
          submit_label: $(this).siblings('span.submit-label').text(),
          debug: true,
          action: action,
          replace_existing_form: true,
          multiple: false
        });
      popup.dialog('open');
  });

});
