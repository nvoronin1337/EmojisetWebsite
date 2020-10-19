$(document).ready(function () {
  let total_results = 0
  let table_id = ""
  let btn_id = ""

  // initialli hide the settings container
  $("#selection_settings_container").hide();

  // read hidden settings <div> contents as a string of HTML code
  let settings = $('#hidden_selection_settings').html();
  let filter_settings = $('#hidden_filter_selection_settings').html();

  // hide the progress bar and the label (discarded tweets)
  let progress_bar = document.getElementById('progress_bar')
  let discarded_tweets_lbl = document.getElementById('discarded_tweets')
  progress_bar.hidden = true
  discarded_tweets_lbl.hidden = true


  /** Sets default dates for the date input fields */
  function set_date() {
    var now = new Date();
    var week_ago = new Date();
    week_ago.setDate(now.getDate() - 7);
    var month_now = (now.getMonth() + 1);
    var month_week_ago = (week_ago.getMonth() + 1);
    var day_now = now.getDate();
    var day_week_ago = week_ago.getDate();

    if (month_now < 10)
      month_now = "0" + month_now;
    if (month_week_ago < 10)
      month_week_ago = "0" + month_week_ago;
    if (day_now < 10)
      day_now = "0" + day_now;
    if (day_week_ago < 10)
      day_week_ago = "0" + day_week_ago;

    var today = now.getFullYear() + '-' + month_now + '-' + day_now;
    var day_week_ago = week_ago.getFullYear() + '-' + month_week_ago + '-' + day_week_ago;
    $('#until-date').val(today);
    $('#since-date').val(day_week_ago);
  }


  /** Displays additional settings for SEARCH (historical stream)*/
  function display_search_settings() {
    if (!$('#selection_settings_container').is(':visible')) {
      $(($("#selection_settings_container"))).empty().append(settings).hide().slideDown();
      set_date();
      $("#near-me").change(function () {
        if (this.checked) {
          $("#city").attr("disabled", true);
        } else {
          $("#city").attr("disabled", false);
        }
      });
    } else {
      $("#selection_settings_container").slideUp();
    }

  }


  /** Displays additional settings for FILTER (real time stream) */
  function display_filter_settings() {
    if (!$('#selection_settings_container').is(':visible')) {
      $(($("#selection_settings_container"))).empty().append(filter_settings).hide().slideDown();
    } else {
      $("#selection_settings_container").slideUp();
    }
  }


  /** 
   * Takes a job result from check_job_status js function and structures it as a HTML table
   *  Also takes an empty string (htmlString) which is then filled with HTML code and returned
   */
  function create_result(message, htmlString) {
    let row_style = 'style="table-row"'
    let counter = 0
    table_id = 'table' + total_results
    btn_id = '#export' + total_results

    htmlString = '<div class="card mb-3">'
    htmlString += '<div class="card-body">'
    htmlString += '<table id="' + table_id + '" style="width: 100%;"><tr><th>Tweet</th><th>Emojiset</th></tr>'
    htmlString += "<colgroup><col span=\"1\" style=\"width: 75%;\"><col span=\"1\" style=\"width: 25%;\"></colgroup>"
    for (let index in message) {
      htmlString += '<tr ' + row_style + '>'
      htmlString += '<td style="padding:0 15px;"><small class="text-muted d-block">' + (message[index])[0] + '</small></td>'
      htmlString += '<td style="padding:0 15px;"><small class="text-muted d-block">' + (message[index])[1] + '</small></td>'
      htmlString += '</tr>'
      counter += 1
      if (counter >= 10) {
        row_style = 'style="display: none"'
      }
    }
    htmlString += '</table></div>'
    htmlString += '<button id="export' + total_results + '" data-export="export" class="btn btn-primary">Download full results</button>'
    htmlString += '</div>'
    total_results++
    return htmlString
  }


  /**
   * Accepts a message (either a result dictionary or a string describing the error)
   * Aceepts a messages cattegory ('success' OR 'danger')
   * Accepts a boolean which specifies if previous alerts should be cleaned (removed from page)
   * Creates a HTML element (either a table using create_result function or a simple error message)
   * Appends HTML element to the result_container div (result placeholder)
   * Creates an event listener for the download results button
   */
  function flash_alert(message, category, clean) {
    if (typeof (clean) === "undefined") clean = true;
    if (clean) {
      remove_alerts();
    }
    if (category == "success") {
      let empty_result = false
      if (Object.keys(message).length == 0) {
        empty_result = true
      }
      let htmlString = ""
      if (!empty_result) {
        htmlString = create_result(message, htmlString)
      } else {
        htmlString = '<div class="card mb-3">'
        htmlString += '<div class="card-body">'
        htmlString += 'There are no tweets matching your keywords!'
        htmlString += '</div></div>'
      }
      $(htmlString).prependTo("#result_container").hide().slideDown();
    } else if (category == "danger") {
      var htmlString = '<div class="card mb-3">'
      htmlString += '<div class="card-body">'
      htmlString += 'Job Failed!'
      htmlString += '</div></div>'
      $(htmlString).prependTo("#result_container").hide().slideDown();
    }

    $(btn_id).click(function () {
      //$("#" + table_id).tableToCSV();
      $("#" + table_id).table2excel({
        filename: "Emojisets.xls"
      });
    });
  }


  /* Used to remove previous alerts from the page */
  function remove_alerts() {
    $(".alert").slideUp("normal", function () {
      $(this).remove();
    });
  }


  /**
   * 
   * @param {*} status_url -> website/status/job_key
   * Called from the submit button event listener
   * Attempts to read json located at the specified URL every 150ms (timeout time can be changed)
   * Json file (our data object) has multiple attributes:
   *  status: job status ('unknown', 'finished', 'failed', or for our default case: queued/started/deferred)
   *  progress: integer (received tweets / total desired tweets) 
   *  discarded_tweets: integer 
   *  result: dictionary in the format index:(tweet, emojiset)
   * Depending on the job status, it either sleeps and runs again, 
   *  or calls flash_alert function with (data.result, 'success') on 'finished'
   *  or calls flash_alert function with ('error message', 'danger') on 'failed' or 'unknown'
   */
  function check_job_status(status_url) {
    $.getJSON(status_url, function (data) {
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
          if (data.discarded_tweets != 0) {
            discarded_tweets_lbl.hidden = false
          }
          discarded_tweets_lbl.innerText = "Discarded tweets: " + data.discarded_tweets
          setTimeout(function () {
            check_job_status(status_url);
          }, 150);
      }
    });
  }


  /**
   * Submit button event listener
   * Sends a POST request an AJAX call to the website/_run_task url (see views.py)
   * POST request includes data from the form on the page
   * Expects to receive back json file
   * IF the AJAX call was successful -> get Location header from the json
   *    call check_job_status function with Location as a parameter
   * IF ERROR log error to the console and return
   */
  $("#submit").on('click', function (e) {
    e.preventDefault()
    $("#submit").attr("disabled", true);
    progress_bar.hidden = false;
    $.ajax({
      //url:  "http://69.43.72.217/_run_task",
      url: "http://127.0.0.1:5000/_run_task",
      data: $("#taskForm").serialize(),
      method: "POST",
      dataType: "json",
      success: function (data, status, request) {
        var status_url = request.getResponseHeader('Location');
        console.log("Status URL: " + status_url)
        check_job_status(status_url);
      },
      error: function (jqXHR, textStatus, errorThrown) {
        console.log(textStatus)
      }
    });
    return false;
  });


  // additional settings button on click event listener
  $("#tweet_selection_settings").on('click', function (e) {
    e.preventDefault()
    let twarc_method = $("#twarc-method option:selected").val();
    if (twarc_method == "search") {
      display_search_settings();
    } else if (twarc_method == "filter") {
      display_filter_settings();
    } else {
      $("#selection_settings_container").slideUp();
    }
  });


  // twarc method selection changed event listener
  $("#twarc-method").change(function () {
    let twarc_method = $("#twarc-method option:selected").val()
    if (twarc_method == 'sample') {
      $("#tweet_selection_settings").attr("disabled", true);
      $("#selection_settings_container").slideUp();
    } else if (twarc_method == 'search') {
      $(($("#selection_settings_container"))).empty().append(settings).hide().slideDown();
      set_date();
      $("#near-me").change(function () {
        if (this.checked) {
          $("#city").attr("disabled", true);
        } else {
          $("#city").attr("disabled", false);
        }
      });
      $("#tweet_selection_settings").attr("disabled", false);
    } else if (twarc_method == 'filter') {
      $(($("#selection_settings_container"))).empty().append(filter_settings).hide().slideDown();
      $("#tweet_selection_settings").attr("disabled", false);
    }
  });

  // Used for properly displaying emoji keyboard
  $("#keywords").emojioneArea({
    pickerPosition: "bottom"
  });
});