function draw_histogram(response) {
    var i, data, keys, buckets, key;

    data = [];
    keys = [];
    buckets = response.aggregations.times.buckets;

    for (i = 0; i < buckets.length; i += 1) {
        data.push(buckets[i].doc_count);
        key = buckets[i].key_as_string.split("T")[0];
        if (i === 0) {
            keys.push("Unknown Date");
        } else {
            keys.push(key);
        }
    }

    $("#histogram").highcharts({
        chart: {
            type: "column",
            height: 200
        },
        title: {
            size: "8px",
            text: "",
            style: {
                fontSize: "10px"
            }
        },
        xAxis: {
            categories: keys,
            labels: {
                enabled: false
            }
        },
        yAxis: {
            min: 1,
            type: "logarithmic",
            minorTickInterval: 0.5,
            tickInterval: 0.5,
            title: {
                text: ""
            }
        },
        series: [
            {
                showInLegend: false,
                name: "Files",
                data: data
            }
        ],
        plotOptions: {
            column: {
                pointPadding: 0,
                borderWidth: 0,
                groupPadding: 0,
                shadow: false,
            }
        }
    });
}

function request_histogram() {
    var xhr, request, response;

    request = {
        "_source": {
            "include": []
        },
        "aggs": {
            "times": {
                "date_histogram": {
                    "field": "start_time",
                    "interval": "week"
                }
            }
        },
        "size": 0
    };

    // Create and send request
    xhr = new XMLHttpRequest();
    xhr.open("POST", es_url, true);
    xhr.send(JSON.stringify(request));

    // Handle the response
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            response = JSON.parse(xhr.responseText);
            draw_histogram(response);
        }
    };
}
