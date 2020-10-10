$(document).ready(function() {
    let total_results = 0
    let progress_bar = document.getElementById('progress_bar')
    let discarded_tweets_lbl = document.getElementById('discarded_tweets')
    progress_bar.hidden = true
    discarded_tweets_lbl.hidden = true
    let table_id = ""
    let btn_id = ""


    function create_result(message, htmlString){
      let row_style = 'style="table-row"'
      let counter = 0
      table_id = 'table' + total_results
      btn_id = '#export' + total_results

      // Creating an HTML <table>
      htmlString = '<div class="card mb-3">'
      htmlString += '<div class="card-body">' 
      htmlString += '<table id="' + table_id + '" style="width: 100%"><tr><th>Tweet</th><th>Emojiset</th></tr>'
      htmlString += "<colgroup><col span=\"1\" style=\"width: 75%;\"><col span=\"1\" style=\"width: 25%;\"></colgroup>"
      for (let index in message){ 
        htmlString += '<tr ' + row_style + '>'
        htmlString += '<td><small class="text-muted d-block">' + (message[index])[0] + '</small></td>'
        htmlString += '<td><small class="text-muted d-block">' + (message[index])[1] + '</small></td>'
        htmlString += '</tr>'
        counter += 1
        if(counter >= 10){
          row_style = 'style="display: none"'
        }
      }
      htmlString += '</table></div>'
      htmlString += '<button id="export' + total_results + '" data-export="export" class="btn btn-primary">Download full results</button>' 
      htmlString += '</div>'
      total_results++
      $(htmlString).prependTo("#result_container").hide().slideDown();  
    }
    
    function flash_alert(message, category, clean) {
      if (typeof(clean) === "undefined") clean = true;
      if(clean) {
        remove_alerts();
      }
      
      if(category == "success"){
        let empty_result = false
        if(Object.keys(message).length == 0){
          empty_result = true
        }
    
          
        let htmlString = ""

        if(!empty_result){
          create_result(message, htmlString)
        }
        else{
          htmlString = '<div class="card mb-3">'
          htmlString += '<div class="card-body">'
          htmlString += 'There are no tweets matching your keywords!' 
          htmlString += '</div></div>'
        }
        $(htmlString).prependTo("#result_container").hide().slideDown();       
      }else if(category == "danger"){
        var htmlString = '<div class="card mb-3">'
        htmlString += '<div class="card-body">'
        htmlString += 'Job Failed!'
        htmlString += '</div></div>'
        $(htmlString).prependTo("#result_container").hide().slideDown();
      }
      
      $(btn_id).click(function(){
        //$("#" + table_id).tableToCSV();
        $("#" + table_id).table2excel({ 
          filename: "Emojisets.xls" 
        }); 
      });
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
            progress_bar.hidden = true
            discarded_tweets_lbl.hidden = true
            $("#submit").attr("disabled", false);
            flash_alert("Unknown job id", "danger");
            break;
          case "finished":
            progress_bar.hidden = true
            discarded_tweets_lbl.hidden = true
            $("#submit").attr("disabled", false);
            flash_alert(data.result, "success");
            break;
          case "failed":
            progress_bar.hidden = true
            discarded_tweets_lbl.hidden = true
            $("#submit").attr("disabled", false);
            flash_alert("Job failed: " + data.message, "danger");
            break;
          default:
            //queued/started/deferred
            $("#progress_bar").val(data.progress)
            if(data.discarded_tweets != 0){
                discarded_tweets_lbl.hidden = false
            }
            discarded_tweets_lbl.innerText = "Discarded tweets: " + data.discarded_tweets
            setTimeout(function() {
              check_job_status(status_url);
            }, 150);
        }
      });
    }
  

    // submit form
    $("#submit").on('click', function(e) {
      e.preventDefault()
      let keywords = $('#keywords').val();
      let twarc_method = $('.twarc_method:checked').val();
      if(keywords || twarc_method == 'sample'){
        $("#submit").attr("disabled", true);
        progress_bar.hidden = false;
        $.ajax({
          //url:  "http://69.43.72.217/_run_task",
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
      }
      else{
        alert("Please enter some keywords!")
      }
      return false;
    });
 

    $("#keywords").emojioneArea({
      pickerPosition: "bottom"
    });
});
