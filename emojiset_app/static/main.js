$(document).ready(function () {
  let total_results = 0
  let table_id = ""
  let btn_download_id = ""
  let btn_delete_id = ""
  let btn_save_id = ""
  let query_id = ""
  let toast_id = ""
  let hidden_toast_div_id = ""

  // hide the progress bar and the label (discarded tweets)
  let progress_bar_div = document.getElementById('progress_bar_div')
  let discarded_tweets_div = document.getElementById('discarded_tweets')
  let cancel_btn = document.getElementById('cancel')

  progress_bar_div.hidden = true
  discarded_tweets_div.hidden = true
  cancel_btn.hidden = true
  $("#cancel_filter").hide()
  $("#cancel_sample").hide()

  $(function () {
    $('[data-toggle="tooltip"]').tooltip()
  })


  /** Sets default dates for the date input fields */
  function set_date() {
    var now = new Date();
    var week_ago = new Date();
    week_ago.setDate(now.getDate() - 6);
    var month_now = (now.getMonth() + 1);
    var month_week_ago = (week_ago.getMonth() + 1);
    var day_now = now.getDate() + 1;
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


  /** 
   * Takes a job result from check_job_status js function and structures it as a HTML table
   *  Also takes an empty string (htmlString) which is then filled with HTML code and returned
   */
  function create_result(message, htmlString) {
    let row_style = 'style="table-row; border: 1px solid #6C757D;"'
    let counter = 0
    table_id = 'table' + total_results
    btn_download_id = 'export' + total_results
    btn_delete_id = 'delete' + total_results
    btn_save_id = 'save' + total_results
    query_id = 'query' + total_results
    toast_id = 'toast' + total_results
    hidden_toast_div_id = 'toast_div' + total_results

    let html_save_btn = '<button id="' + btn_save_id + '" type="button" style="padding: 0; border: none; background: none;"><span class="badge badge-secondary"><i class="fa fa-save"></i> Query</span></button>'
    let html_delete_btn = '<button id="' + btn_delete_id + '" type="button" class="close" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
    let html_download_btn = '<button id="' + btn_download_id + '" data-export="export" class="btn btn-success">Download full results</button>'
    let html_hidden_query = '<div id="' + query_id + '" style="display:none;">' + message.query + '</div>'

    let hidden_toast = '<div id="' + hidden_toast_div_id + '" style="display: none;">' +
      '<div aria-live="polite" aria-atomic="true" style="position: relative; min-height: 100px;">' +
      '<div id="' + toast_id + '" class="toast" data-delay="3000" style="position: absolute; top: 0; right: 0;">' +
      '<div class="toast-header">' +
      '<strong class="mr-auto">Emojiset 🙂</strong>' +
      '<button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span>' +
      '</button>' +
      '</div>' +
      '<div class="toast-body">' +
      'Your query has been saved!' +
      '</div>' +
      '</div>' +
      '</div>' +
      '</div>'


    htmlString = '<div id="result' + total_results + '" class="card mb-4">'
    htmlString += '<div class="card-body">'
    htmlString += html_delete_btn
    htmlString += hidden_toast
    htmlString += '<div class="card-body">'
    htmlString += '<table id="' + table_id + '" style="width: 100%;  ">'
    htmlString += '<thead>'
    htmlString += '<tr><th colspan="2" style="font-weight: normal;">' + html_save_btn + '</th></tr>'
    htmlString += '<tr><th scope="col" style="text-align:center">Tweet</th><th scope="col" style="text-align:center">Emojiset</th></tr>'
    htmlString += '</thead>'
    htmlString += "<colgroup><col span=\"1\" style=\"width: 75%;\"><col span=\"1\" style=\"width: 25%;\"></colgroup>"
    for (let index in message.result) {
      htmlString += '<tr ' + row_style + '>'
      htmlString += '<td style="padding: 10px; border: 1px solid #6C757D;"><small class="text-muted d-block">' + (message.result[index])[0] + '</small></td>'
      htmlString += '<td style="padding: 10px; border: 1px solid #6C757D; text-align:center"><small class="text-muted d-block">' + (message.result[index])[1] + '</small></td>'
      htmlString += '</tr>'
      counter += 1
      if (counter == 10) {
        row_style = 'style="display: none"'
      }
    }
    htmlString += '</table></div></div>'
    htmlString += '<div class="card-footer">'
    htmlString += html_download_btn
    htmlString += html_hidden_query
    htmlString += '</div></div>'
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
      if (Object.keys(message.result).length == 0) {
        empty_result = true
      }
      let htmlString = ""
      if (!empty_result) {
        htmlString = create_result(message, htmlString)
      } else {}
      $(htmlString).prependTo("#result_container").hide().slideDown();

    } else if (category == "danger") {}

    $("#" + btn_save_id).click(function (e) {
      e.preventDefault()
      let query_id = $(this).attr("id").replace('save', 'query')
      let hidden_toast_div = $(this).attr("id").replace('save', 'toast_div')
      let toast_id = $(this).attr("id").replace('save', 'toast')

      let json_query = $('#' + query_id).html()
      $.ajax({
        type: "POST",
        url: document.location.href + '/save_query',
        data: {
          'query': json_query
        },
        dataType: 'json',
        success: function (data, status, request) {
          $('#' + hidden_toast_div).show()
          $('#' + toast_id).toast('show')
        },
        error: function (jqXHR, textStatus, errorThrown) {
          console.log(textStatus)
        }
      });
    });

    // create download button event listener
    $("#" + btn_download_id).click(function (e) {
      e.preventDefault()
      let id = $(this).attr("id").replace('export', '')
      $("#table" + id).table2excel({
        filename: "Emojisets.xls"
      });
    });

    // create delete button event listener
    $("#" + btn_delete_id).click(function (e) {
      e.preventDefault()
      let id = $(this).attr("id").replace('delete', '')
      $("#result_container").find("#result" + id).remove();
    });

    $('#' + toast_id).on('hidden.bs.toast', function (e) {
      e.preventDefault()
      let id = $(this).attr("id").replace('toast', '')
      $('#toast_div' + id).hide()
    })
  }

  /* Used to remove previous alerts from the page */
  function remove_alerts() {
    $(".alert").slideUp("normal", function () {
      $(this).remove();
    });
  }


  /**
   * 
   * @param status_url -> website/status/job_key
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
          progress_bar_div.hidden = true;
          discarded_tweets_div.hidden = true;
          cancel_btn.hidden = true;
          $("#cancel_filter").hide()
          $("#cancel_sample").hide()
          $("#submit").show()
          $("#submit_filter").show()
          $("#submit_sample").show()
          break;
        case "finished":
          progress_bar_div.hidden = true;
          discarded_tweets_div.hidden = true;
          cancel_btn.hidden = true;
          $("#cancel_filter").hide()
          $("#cancel_sample").hide()
          $("#submit").show()
          $("#submit_filter").show()
          $("#submit_sample").show()
          if (!data.cancel_flag) {
            flash_alert(data, "success");
          }
          break;
        case "failed":
          progress_bar_div.hidden = true;
          discarded_tweets_div.hidden = true;
          cancel_btn.hidden = true;
          $("#cancel_filter").hide()
          $("#cancel_sample").hide()
          $("#submit").show()
          $("#submit_filter").show()
          $("#submit_sample").show()
          break;
        default:
          //queued/started/deferred
          $(".progress-bar").css('width', data.progress + '%').attr('aria-valuenow', data.progress);
          $(".progress-bar small").text(data.progress.toFixed(1) + '%');
          if (data.discarded_tweets != 0) {
            discarded_tweets_div.hidden = false
          }
          $('#discarded_tweets_lbl span').text(data.discarded_tweets);
          setTimeout(function () {
            check_job_status(status_url);
          }, 150);
      }
    });
  }


  function cancel_job(cancel_url) {
    $.getJSON(cancel_url, function (response) {

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
    $("#submit").hide()
    $("#submit_filter").hide()
    $("#submit_sample").hide()
    progress_bar_div.hidden = false;
    // ---document.location.href returns the url at which the user is currently at---*
    let run_task_url = document.location.href + "/_run_small_task"
    $.ajax({
      url: run_task_url,
      data: $("#taskForm").serialize(),
      method: "POST",
      dataType: "json",
      success: function (data, status, request) {
        let status_url = request.getResponseHeader('Status');
        let cancel_url = request.getResponseHeader('Cancel');
        console.log("Status URL: " + status_url)

        // Add cancel button event listener
        cancel_btn.hidden = false;
        $('#cancel').on('click', function (e) {
          e.preventDefault()
          cancel_job(cancel_url)
        });
        check_job_status(status_url);
      },
      error: function (jqXHR, textStatus, errorThrown) {
        console.log(textStatus)
      }
    });
    return false;
  });

  /**
   * Submit button event listener
   * Sends a POST request an AJAX call to the website/_run_task url (see views.py)
   * POST request includes data from the form on the page
   * Expects to receive back json file
   * IF the AJAX call was successful -> get Location header from the json
   *    call check_job_status function with Location as a parameter
   * IF ERROR log error to the console and return
   */
  $("#submit_filter").on('click', function (e) {
    e.preventDefault()
    $("#submit").hide()
    $("#submit_filter").hide()
    $("#submit_sample").hide()
    progress_bar_div.hidden = false;
    // ---document.location.href returns the url at which the user is currently at---*
    let run_task_url = document.location.href + "/_run_small_task"
    $.ajax({
      url: run_task_url,
      data: $("#taskForm_filter").serialize(),
      method: "POST",
      dataType: "json",
      success: function (data, status, request) {
        let status_url = request.getResponseHeader('Status');
        let cancel_url = request.getResponseHeader('Cancel');
        console.log("Status URL: " + status_url)

        // Add cancel button event listener
        $("#cancel_filter").show()
        $('#cancel_filter').on('click', function (e) {
          e.preventDefault()
          cancel_job(cancel_url)
        });
        check_job_status(status_url);
      },
      error: function (jqXHR, textStatus, errorThrown) {
        console.log(textStatus)
      }
    });

    return false;
  });

  /**
   * Submit button event listener
   * Sends a POST request an AJAX call to the website/_run_task url (see views.py)
   * POST request includes data from the form on the page
   * Expects to receive back json file
   * IF the AJAX call was successful -> get Location header from the json
   *    call check_job_status function with Location as a parameter
   * IF ERROR log error to the console and return
   */
  $("#submit_sample").on('click', function (e) {
    e.preventDefault()
    $("#submit").hide()
    $("#submit_filter").hide()
    $("#submit_sample").hide()
    progress_bar_div.hidden = false;
    // ---document.location.href returns the url at which the user is currently at---*
    let run_task_url = document.location.href + "/_run_small_task"
    $.ajax({
      url: run_task_url,
      data: $("#taskForm_sample").serialize(),
      method: "POST",
      dataType: "json",
      success: function (data, status, request) {
        let status_url = request.getResponseHeader('Status');
        let cancel_url = request.getResponseHeader('Cancel');
        console.log("Status URL: " + status_url)

        // Add cancel button event listener
        $("#cancel_sample").show()
        $('#cancel_sample').on('click', function (e) {
          e.preventDefault()
          cancel_job(cancel_url)
        });
        check_job_status(status_url);
      },
      error: function (jqXHR, textStatus, errorThrown) {
        console.log(textStatus)
      }
    });

    return false;
  });

  $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
    $('.form-group input[type="number"]').val('');
    $('.form-group input[type="datetime-local"]').val('');
    $('.form-group input[type="text"]').val('');
    $('.form-group input[type="date"]').val('');
  });
  //find a way to set checkboxes to default-->
  $('a[data-toggle="toggle"]').on('shown.bs.tab', function (e) {
    $('.form-group input[type="checkbox"]').val(on);
  });

  // Used for properly displaying emoji keyboard
  $("#keywords").emojioneArea({
    pickerPosition: "bottom",
    buttonTitle: "Filter by emojis",
    filtersPosition: "bottom",
  });

  $("#keywords_filter").emojioneArea({
    pickerPosition: "bottom",
    inline: true
  });

  $("#keywords_sample").emojioneArea({
    pickerPosition: "bottom",
    inline: true
  });

});