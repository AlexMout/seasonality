

function get_contracts(maturities){
    //Get selected element :
    var selected_contracts = $('#contracts_available').val();

    //Empty the current options displayed if any:
    $('#maturity_available').empty();

    for(var index in maturities[selected_contracts]){
        $('#maturity_available').append($('<option>',{text:maturities[selected_contracts][index]}));
    }

    if (selected_contracts == "Cal" || selected_contracts == "Cal Spread"){
        $('#maturity_available').prop("disabled",true);
    }
    else{
        $('#maturity_available').prop("disabled",false);
    }
}


