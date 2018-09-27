var d3 = Plotly.d3;
var WIDTH_IN_PERCENT_OF_PARENT = 80,
    HEIGHT_IN_PERCENT_OF_PARENT = 100;

function create_graph_plotly(quotes, dates, product, contract, is_overlap)
{
    /* Structure of quotes:
    { 'CAL14' : [close,close...],
    'CAL15': [close,close...],
    ...}

    Structure of dates
    {  'CAL14' : [date1,date2...], ...}
    */

    var ell = document.getElementById("chart_container")
    var gd3 = d3.select(ell)
    .style({
        width: WIDTH_IN_PERCENT_OF_PARENT + '%',
        'margin-left': 0,

        height: HEIGHT_IN_PERCENT_OF_PARENT + '%',
        'margin-top': 0,
    });


    var gd = gd3.node();
    var data = [];

    for(var key in quotes)
    {
        var trace = {
        x: dates[key],
        y: quotes[key],
        mode: 'lines',
        type: 'scatter',
        name:key,
        };

        data.push(trace)
    }

    var layout = {
        /*margin:{
            t: 90,
            b: 90,
            l: 60,
            r: 20,
            },*/
        xaxis: {
            title: 'Date',
            titlefont: {
                color: 'white'
                },
            tickfont: {
                color: 'white'
                },
            //tickformat:"%B",
            },
        yaxis: {
        title: 'Price',
        titlefont: {
            color: 'white'
        },
        tickfont: {
            color: 'white'
            },
        },
        paper_bgcolor:'rgba(0,0,0,0)',
        plot_bgcolor:'rgba(0,0,0,0)',
        title: product + " - " + contract,
        titlefont: {
            size: 18,
            color: 'white',
            },
        showlegend: true,
        legend: {"orientation": "v",font:{color:'white'}},
        hovermode: true
};

if (is_overlap == "True")
{
    layout["xaxis"]["tickformat"] = "%B";
}

plot = Plotly.plot(gd, data, layout, {showLink: false, displayModeBar: false});

$(window).resize(function(){
    Plotly.Plots.resize(gd);
});
}