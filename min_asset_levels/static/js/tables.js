var id;
var min_qty_val;
var asset_name;

function displayAlert(message) {
  $('#model-alert').show();
  $('#model-alert').text(message);
  setTimeout(function(){
    $('#model-alert').hide();
  }, 2000)
}


  $('#modal').on('show.bs.modal', function(){
    // load form
    fetch('./asset_models/editminqty').then(function(result) {
      result.text().then(function(r) {
       
        // Hide the alert
        $('#model-alert').hide();

        // Load form data
        $('#django-form').html(r);
        var $form = $('#django-form form');
        
        // Initial input value
        $('#id_min_qty').val(min_qty_val);

        // Display asset name
        $('#form_asset_name').text(asset_name)
        $('#id_min_qty').select()

        // submit button sumbits form
        $('#sub').click(() => $form.submit());
        $form.submit(function(x) {
          
        x.preventDefault();

        var data = new FormData($form[0]);

          $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: `${$form.attr('action')}/${id}`,
            data: data,
            processData: false,
            contentType: false,
            cache: false,
            timeout: 800000,
            dataType: 'json',
            success: function (e) {
 
              // Check for validation
              if (e.hasOwnProperty('success')){
                // if all is good close modal
                $('#modal').modal('hide');
                $("#table").bootstrapTable('refresh')
              }else{
                displayAlert(e.error)
              }
            },
            error: function (e) {
              displayAlert("An error occurred, please try again.")
            }
          });
        })
      })
    })
  })

  // Bind the model to the tr
  $("#table").on('click-row.bs.table', function(_a, row){
      //console.log(row)
      id = row.id;
      min_qty_val = row.model_min_qty
      asset_name = row.model_manufacturer_name + " " + row.model_name + " " + row.model_number
      $('#modal').modal('show');  
      $('#orderModal').data('orderid',$(this).data('id'));
  });
  
