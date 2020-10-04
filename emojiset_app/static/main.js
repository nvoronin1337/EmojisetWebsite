$(document).ready(function() {

    function flash_alert(message, category, clean) {
      if (typeof(clean) === "undefined") clean = true;
      if(clean) {
        remove_alerts();
      }
       
      var htmlString = '<div class="card mb-3">'
      htmlString += '<div class="card-body">' 
      for (let tweet in message){  
        htmlString += '<small class="text-muted d-block">'
        htmlString += tweet + ": " + message[tweet]
        htmlString += '</small>'
      }
      htmlString += '</div>'
      htmlString += '</div>'
      $(htmlString).prependTo("#result_container").hide().slideDown();
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
            flash_alert("Unknown job id", "danger");
            break;
          case "finished":
            flash_alert(data.result, "success");
            break;
          case "failed":
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
      $.ajax({
        url:  "http://127.0.0.1:5000/_run_task",
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
});
