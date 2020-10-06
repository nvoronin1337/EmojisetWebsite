$(document).ready(function() {
    let total_results = 0
    let loader = document.getElementById("loader")
    loader.hidden = true

    function flash_alert(message, category, clean) {
      if (typeof(clean) === "undefined") clean = true;
      if(clean) {
        remove_alerts();
      }
      
      let table_id = 'table' + total_results
      let btn_id = '#export' + total_results
    
      var htmlString = '<div class="card mb-3">'
      htmlString += '<div class="card-body">' 
      htmlString += '<table id="' + table_id + '"><tr><th>Tweet</th><th>Emojiset</th></tr>'
      
      let row_style = 'style="table-row"'

      let counter = 0
      for (let tweet in message){ 
        htmlString += '<tr ' + row_style + '>'
        htmlString += '<td><small class="text-muted d-block">' + tweet + '</small></td>'
        htmlString += '<td><small class="text-muted d-block">' + message[tweet] + '</small></td>'
        htmlString += '</tr>'
        
        counter += 1
        if(counter >= 10){
          row_style = 'style="display: none"'
        }
      }

      htmlString += '</table></div>'
      htmlString += '<button id="export' + total_results + '" data-export="export" class="btn btn-primary">Download full results</button>' 
      htmlString += '</div>'
      
      $(htmlString).prependTo("#result_container").hide().slideDown();
      
      $(btn_id).click(function(){
        $("#" + table_id).tableToCSV();
      });

      total_results++
    }

    function remove_alerts() {
      $(".alert").slideUp("normal", function() {
        $(this).remove();
      });
    }

    function check_job_status(status_url) {
      $.getJSON(status_url, function(data) {
        switch (data.status) {
          case "unknown":
            loader.hidden = true
            flash_alert("Unknown job id", "danger");
            break;
          case "finished":
            loader.hidden = true
            flash_alert(data.result, "success");
            break;
          case "failed":
            loader.hidden = true
            flash_alert("Job failed: " + data.message, "danger");
            break;
          default:
            // queued/started/deferred
            setTimeout(function() {
              check_job_status(status_url);
            }, 500);
        }
      });
    }
  
    // submit form
    $("#submit").on('click', function(e) {
      e.preventDefault()
      // add loading icon
      loader.hidden = false
      $.ajax({
        url:  "http://69.43.72.217/_run_task",
        data: $("#taskForm").serialize(),
        method: "POST",
        dataType: "json",
        success: function(data, status, request) {
          var status_url = request.getResponseHeader('Location');
          console.log("Status URL: " + status_url)
          check_job_status(status_url);
        },
        error: function(jqXHR, textStatus, errorThrown) {
          console.log("error")
        }
      });
    });

    
    $("#keywords").emojioneArea({
      pickerPosition: "bottom"
    });
    
});
