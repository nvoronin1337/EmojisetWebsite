$(document).ready(function () {
    $('#submit').click(function(e) {
        e.preventDefault()
        let bias = $('#bias').val();
        let adopter = $('#adopter').val();
        let rejector = $('#rejector').val();
        let q_group = $('#q_group').val();

        if(bias != "" && adopter != "" && rejector != "" && q_group != ""){
            let run_si_model_url = location.href + "/mmr"
            
            $.ajax({
                url: run_si_model_url,
                data: {
                    'bias': bias,
                    'adopter': adopter,
                    'rejector': rejector,
                    'q_group': q_group
                },
                method: "POST",
                dataType: "json",
                success: function (data, status, request) {
                    $('#model').html(data.plot_html)
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.log(textStatus)
                }
            });
        }else{
            alert("Please fill all parameters");
        }
    });
});
