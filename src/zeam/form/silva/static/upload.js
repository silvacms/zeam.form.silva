$(document).ready(function() {

  var uploadButtons = $('a.open-upload-popup');
  uploadButtons.button({ icons: {primary:'ui-icon-document'}});

  uploadButtons.live('click', function(){
      var popup = $('<div.upload-popup style="display:none"><p/></div>');
      popup.appendTo(document.body);

      var popupButtons = {};

      popup.dialog({
          title: $(this).text(),
          autoOpen: false,
          modal: true,
          zIndex: 12001,
          buttons: popupButtons
      });

      var action = $('a#content-url').attr('href') + '/++rest++upload/';
      var uploadForm = $('<form enctype="multipart/form-data'+
                            'method="POST"' +
                            'action="." >' +
                            '<input type="file" name="file" />' +
                         '</form>');
      uploadForm.appendTo(popup.children('p'));

      $(document).one('upload-finished', function(event, data){
          var path = data['paths'][0];
          var filename = path.replace(/^.*[\/\\](.*)$/, '$1');
          $(this).siblings('input:hidden').first().val(path);
          $(this).siblings('.display-value').first().text(filename);
          popup.dialog('destroy');
      }.scope(this));

      popup.children('p').fileUpload({
          submit_label: $(this).siblings('span.submit-label').text(),
          debug: true,
          action: action,
          replace_existing_form: true,
          multiple: false,
          dialogElement: popup
        });
      popup.dialog('open');
  });

});
