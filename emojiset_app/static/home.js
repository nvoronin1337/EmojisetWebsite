function GoToEmojiset() {
    let exmojiset_url = document.location.href.split('#')[0] + "emojiset"
    location.href = exmojiset_url
}

$(document).ready(function () {
    $('#send').on('click', function(e){
        e.preventDefault()
        let contact_us_url = location.href + "/contact_us"
        $.ajax({
			url: contact_us_url,
			data: $("#contact_form").serialize(),
			method: "POST",
			dataType: "json",
			success: function (data, status, request) {
				$('contact_modal').modal('toggle')
			},
			error: function (jqXHR, textStatus, errorThrown) {
				console.log(textStatus)
			}
		});
    });
});