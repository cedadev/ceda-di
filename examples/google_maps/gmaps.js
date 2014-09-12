/*---------------------------- Setup ----------------------------*/
// Set up constants
var es_url = "http://fatcat-test.jc.rl.ac.uk:9200/badc/eufar/_search";
var wps_url = "http://ceda-wps2.badc.rl.ac.uk:8080/submit/form?proc_id=PlotTimeSeries&FilePath="
var geocoder = new google.maps.Geocoder();
var map = new google.maps.Map(document.getElementById('map'), {
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    zoom: 6
});

// Centre the map on Hungary initially
geocoder.geocode(
    {
        "address": "Lake Balaton, Hungary"
    },
    function(results, status) {
        if (status === "OK") {
            map.setCenter(results[0].geometry.location);
        }
    }
);

var polygons = [] // Array of polygon shapes drawn from ES requests
var info_windows = [] // Array of InfoWindows (one for each polygon)

// Additional filter parameters
var additional_filter_params = null;

// Set up location 'search' button
$("#location_search").click(
    function () {
        location_search();
    }
);

// Clears all input values
$("#clearfil").click(
    function () {
        clear_filters();
    }
);

// Constructs query filters from input values
$("#applyfil").click(
    function () {
        apply_filters();
    }
);

// Override location form submission on 'enter'
$("#location").keypress(
    function (e) {
        charcode = e.charCode || e.keyCode || e.which;
        if (charcode == 13) {
            location_search();
            return false;
        }
    }
);


/*---------------------------- Functions ----------------------------*/

// Checks if a given item is in an array
function is_in(array, item) {
    for (i = 0; i < array.length; i++) {
        if (i === array[i]) {
            return true;
        }
    }
    return false;
}

// Location search
function location_search() {
    loc = $("#location").val()
    if (loc === "") {
        alert("Please enter a value into the 'Location' box.");
    } else {
        geocoder.geocode({
            "address": loc,
        },
        function(results, status) {
            if (status === "OK") {
                new_centre = results[0].geometry.location;
                // Centre map on new location
                map.panTo(new_centre);
            } else {
                alert("Could not find '" + loc + "'");
            }
        });
    }
}

// Clears additional filters from ES request
function clear_filters() {
    additional_filter_params = null;

    $("#ftext").val("");
    $("#start_time").val("");
    $("#end_time").val("");

    redraw_map();
}

// Applies additional filters to ES request
function apply_filters() {
    additional_filter_params = [];

    // Free text search
    ftext_filt = {};
    ftq = $("#ftext").val();
    if (ftq.length > 0) {
        ftext_filt = {
            "term": {
                "_all": ftq
            }
        }
        additional_filter_params.push(ftext_filt);
    }

    // Time range
    start_time_query = {};
    start_time = $("#start_time").val();
    if (start_time.length > 0) {
        start_time_query = {
            "range": {
                "temporal.start_time": {
                    "from": start_time
                }
            }
        }
    }

    end_time_query = {};
    end_time = $("#end_time").val();
    if (end_time.length > 0) {
        end_time_query = {
            "range": {
                "temporal.start_time": {
                    "to": end_time
                }
            }
        }
    }

    // Combine time restrictions into single filter
    time_queries = {};
    if (! $.isEmptyObject(start_time_query)) {
        $.extend(true, time_queries, start_time_query);
    }

    if (! $.isEmptyObject(end_time_query)) {
       $.extend(true, time_queries, end_time_query);
    }

    // Add time filter to list of search criteria
    if (! $.isEmptyObject(time_queries)) {
        additional_filter_params.push(time_queries);
    }
    redraw_map();
}

// Creates an ES geo_shape filter query based on a bounding box
function create_es_request(bbox, offset) {
    temp_ne = bbox.getNorthEast();
    temp_sw = bbox.getSouthWest();

    // Build search extent using NW/SE and lng/lat format
    nw = [temp_sw.lng().toString(),
          temp_ne.lat().toString()];
    se = [temp_ne.lng().toString(),
          temp_sw.lat().toString()];

    // Construct request for ElasticSearch
    request = {
        "_source": {
            "include": [
                "data_format.format",
                "file.filename",
                "file.path",
                "spatial.geometries.bbox",
                "temporal"
            ]
        },
        "filter": {
            "bool": {
                "_cache": true,
                "must": [
                    {
                        "geo_shape": {
                            "bbox": {
                                "shape": {
                                    "type": "envelope",
                                    "coordinates": [nw, se]
                                }
                            }
                        }
                    }
                ],
                "must_not": [
                    {
                        "missing": {
                            "field": "eufar.spatial.geometries.hull.type",
                        }
                    }
                ]
            }
        },
        "size": 20
    };

    // Add any extra user-defined filters
    if (additional_filter_params !== null) {
        for (i in additional_filter_params) {
            request.filter.bool.must.push(additional_filter_params[i]);
        }
    }

    return request;
};

// Construct a google.maps.Polygon object from a bounding box
function construct_polygon(bbox) {
    vertices = [];
    vertices.push(new google.maps.LatLng(bbox[0][1], bbox[0][0]));
    vertices.push(new google.maps.LatLng(bbox[1][1], bbox[1][0]));
    vertices.push(new google.maps.LatLng(bbox[3][1], bbox[3][0]));
    vertices.push(new google.maps.LatLng(bbox[2][1], bbox[2][0]));
    polygon = new google.maps.Polygon({
        paths: vertices,
        geodesic: false,
        strokeColor: "#FF0000",
        strokeWeight: 1,
        strokeOpacity: 1.0,
        fillColor: "#FF0000",
        fillOpacity: 0.1
    });

    return polygon
}

// Construct an InfoWindow from a search hit, containing useful info
function construct_info_window(hit) {
    content = "<section><p><strong>Filename: </strong>" +
              hit.file.filename + "</p>"

    if (hit.temporal) {
        content += "<p><strong>Start Time: </strong>" +
                    hit.temporal.start_time + "</p>" +
                    "<p><strong>End Time: </strong>" +
                    hit.temporal.end_time + "</p>"
    }

    content += "<p><a href=\"http://badc.nerc.ac.uk/browse" +
                   hit.file.path + "\">Get data</a></p>"
                   
    if (hit.data_format.format === "NetCDF") {
        content += "<p><a href=\"" + wps_url + hit.file.path + 
                       "\" target=\"_blank\">Plot time-series</a></p>"
    }
    
    content += "</section>"
    
    info = new google.maps.InfoWindow({
        content: content
    });

    return info;
}

function draw_polygons(hits) {
    for (i in hits) {
        hit = hits[i]._source;
        bbox = hit.spatial.geometries.bbox.coordinates;

        // Construct and display polygon
        polygon = construct_polygon(bbox);
        polygon.setMap(map);
        polygons.push(polygon);

        // Add info window
        iw = construct_info_window(hits[i]._source);
        info_windows.push(iw);
    }

    // Add a listener function to polygon that opens a new
    // InfoWindow on top of the polygon that was clicked
    // (closes all other InfoWindows first)
    for (i in info_windows) {
        google.maps.event.addListener(
            polygons[i], 'click',
            (function(i, e) {
                return function(e) {
                    for (j in info_windows) {
                        info_windows[j].close()
                    }
                    info_windows[i].open(map, null);
                    info_windows[i].setPosition(e.latLng);
                }
            })(i)
        );
    }
}

// Search ES for data (and display received data asynchronously)
function search_es_bbox(bbox) {
    // Create and send request
    xhr = new XMLHttpRequest();
    xhr.open("POST", es_url, true);

    request = create_es_request(bbox);
    xhr.send(JSON.stringify(request));

    $("#loading").show();

    // Handle the response
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            $("#loading").hide();

            response = JSON.parse(xhr.responseText);
            if (response.hits) {
                $("#resptime").html(response.took);
                // Update "number of hits" field in sidebar
                $("#numresults").html(response.hits.total);

                // Loop through each hit, drawing as necessary
                hits = response.hits.hits;
                draw_polygons(hits);
            }
        }
    }
}

// Redraw the map (inc. polygons, etc)
function redraw_map() {
    // Clean up old polygons and info windows
    for (p in polygons) {
        polygons[p].setMap(null);
    }

    for (i in info_windows) {
        info_windows[i].close();
    }

    polygons = [];
    info_windows = [];

    // Make ES request
    bounds = map.getBounds();
    search_es_bbox(bounds);

    // Update bounding coordinates on sidebar
    $("#ge_northeast").html(
        bounds.getNorthEast().toUrlValue(3).replace(",", ", ")
    );
    $("#ge_southwest").html(
        bounds.getSouthWest().toUrlValue(3).replace(",", ", ")
    );

    // Rate-limit requests to ES to 1 per second
    window.setTimeout(function () {
        add_bounds_changed_listener(map)
    }, 1000);
}


// Add a listener to make an ES data request when the map bounds change
function add_bounds_changed_listener(map) {
    google.maps.event.addListenerOnce(map, 'bounds_changed',
        function() {
            redraw_map();
        }
    );
}

// Start the main "bounds_changed" listener loop
add_bounds_changed_listener(map);
