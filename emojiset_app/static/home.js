function GoToEmojiset() {
    let emojiset_url = document.location.href.split('#')[0] + "emojiset"
    location.href = emojiset_url
}

$(document).ready(function () {
    $('#send').on('click', function(e){
		e.preventDefault()
		$('#contact_modal').modal('show'); 
        let contact_us_url = location.href + "/contact_us"
        $.ajax({
			url: contact_us_url,
			data: $("#contact_form").serialize(),
			method: "POST",
			dataType: "json",
			success: function (data, status, request) {
				console.log('mail sent')
			},
			error: function (jqXHR, textStatus, errorThrown) {
				console.log(textStatus)
			}
		});
    });
});