/*jslint browser: true, devel: true, sloppy: true*/
/*global google, $ */

/*---------------------------- Setup ----------------------------*/
// Constants
var es_url = "http://fatcat-test.jc.rl.ac.uk:9200/badc/eufar/_search";
var wps_url = "http://ceda-wps2.badc.rl.ac.uk:8080/submit/form?proc_id=PlotTimeSeries&FilePath=";
var geocoder = new google.maps.Geocoder();
var map = new google.maps.Map(
    document.getElementById('map'),
    {
        mapTypeId: google.maps.MapTypeId.TERRAIN,
        zoom: 4
    }
);

// Colour palette from here: http://bit.ly/1wLGsBG
var path_colours = ["#4D4D4D", "#5DA5DA", "#FAA43A",
                    "#60BD68", "#F17CB0", "#B2912F",
                    "#B276B2", "#DECF3F", "#F15854"]

// Global arrays
window.polygons = []; // Array of polygon shapes drawn from ES requests
window.info_windows = []; // Array of InfoWindows (one for each polygon)

/*---------------------------- Functions ----------------------------*/
String.prototype.hashCode = function () {
    // Please see: http://bit.ly/1dSyf18 for original
    var hash = 0;
    if (this.length == 0) return hash;
    for (i = 0; i < this.length; i++) {
        c = this.charCodeAt(i);
        hash = ((hash << 5) - hash) + c;
    }
    return hash;
}

function location_search() {
    var loc = $("#location").val();
    if (loc === "") {
        alert("Please enter a value into the 'Location' box.");
    } else {
        geocoder.geocode({
            "address": loc
        },
            function (results, status) {
                if (status === "OK") {
                    var new_centre = results[0].geometry.location;
                    // Centre map on new location
                    map.panTo(new_centre);
                } else {
                    alert("Could not find '" + loc + "'");
                }
            }
        );
    }
}

function get_text_filters() {
    full_text_filter = $("#ftext").val();
    if (full_text_filter.length > 0) {
        return {
            "term": {
                "_all": full_text_filter
            }
        };
    }
}

// Construct a google.maps.Polygon object from a bounding box
function construct_polygon(bbox, hit_id) {
    var vertices, polygon;

    vertices = [];
    for (i = 0; i < bbox.length; i += 1) {
        vertices.push(new google.maps.LatLng(bbox[i][1], bbox[i][0]));
    }

    // Pick a colour for the line based on hash value of _id
    index = (hit_id.hashCode() % path_colours.length);
    if (index < 0)  index = -index;
    lineColor = path_colours[index];

    polygon = new google.maps.Polyline({
        path: vertices,
        geodesic: true,
        strokeColor: lineColor,
        strokeWeight: 5,
        strokeOpacity: 0.8
    });

    return polygon;
}

// Construct an InfoWindow from a search hit, containing useful info
function construct_info_window(hit) {
    var content, info;

    content = "<section><p><strong>Filename: </strong>" + hit.file.filename + "</p>";

    if (hit.temporal) {
        content += "<p><strong>Start Time: </strong>" +
                    hit.temporal.start_time + "</p>" +
                    "<p><strong>End Time: </strong>" +
                    hit.temporal.end_time + "</p>";
    }

    if (hit.misc.flight_num) {
        content += "<p><strong>Flight Num: </strong>\"" +
                    hit.misc.flight_num + "\"</p>"
    }

    if (hit.misc.organisation) {
        content += "<p><strong>Organisation: </strong>\"" +
                    hit.misc.organisation + "\"</p>"
    }

    content += "<p><a href=\"http://badc.nerc.ac.uk/browse" +
                   hit.file.path + "\">Get data</a></p>";

    if (hit.data_format.format.search("RAF") > 0) {
        content += "<p><a href=\"" + wps_url +
            hit.file.path + "\" target=\"_blank\">Plot time-series</a></p>";
    }

    content += "</section>";

    info = new google.maps.InfoWindow({content: content});
    return info;
}

function draw_polygons(hits) {
    var i, j, polygon, hit, bbox, iw;

    for (i = 0; i < hits.length; i += 1) {
        hit = hits[i]._source;
        hit_id = hits[i]._id;
        bbox = hit.spatial.geometries.summary.coordinates;

        // Construct and display polygon
        polygon = construct_polygon(bbox, hit_id);
        polygon.setMap(map);
        window.polygons.push(polygon);

        // Add info window
        iw = construct_info_window(hits[i]._source);
        window.info_windows.push(iw);
    }

    // Add a listener function to polygon that opens a new
    // InfoWindow on top of the polygon that was clicked
    // (closes all other InfoWindows first)
    for (i = 0; i < hits.length; i += 1) {
        google.maps.event.addListener(window.polygons[i], 'click',
            (function (i, e) {
                return function (e) {
                    for (j = 0; j < window.info_windows.length; j += 1) {
                        window.info_windows[j].close();
                    }
                    window.info_windows[i].open(map, null);
                    window.info_windows[i].setPosition(e.latLng);
                };
            }
        (i)));
    }
}

// Creates an ES geo_shape filter query based on a bounding box
function create_es_request(bbox, offset) {
    var temp_ne, temp_sw, nw, se, request, i;

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
                "misc",
                "spatial.geometries.summary",
                "temporal"
            ]
        },
        "filter": {
            "and": {
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
                ]
            }
        },
        "size": 30
    };

    // Add any extra user-defined filters
    tf = get_text_filters();
    if (tf) {
        request.filter.and.must.unshift(tf);
    }

    return request;
}

// Search ES for data (and display received data asynchronously)
function search_es_bbox(bbox) {
    var xhr, request, response, hits;

    // Create and send request
    xhr = new XMLHttpRequest();
    xhr.open("POST", es_url, true);

    request = create_es_request(bbox);
    xhr.send(JSON.stringify(request));

    // Handle the response
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
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
    };
}

function cleanup() {
    var p, i;

    // Clean up old polygons and info windows
    for (p = 0; p < window.polygons.length; p += 1) {
        window.polygons[p].setMap(null);
    }

    for (i = 0; i < window.info_windows.length; i += 1) {
        window.info_windows[i].close();
    }

    window.polygons = [];
    window.info_windows = [];
}

// Redraw the map (inc. polygons, etc)
function redraw_map() {
    var bounds;

    cleanup();

    // Make ES request
    bounds = map.getBounds();
    search_es_bbox(bounds);

    // Rate-limit requests to ES to 1 per second
    window.setTimeout(function () {
        add_bounds_changed_listener(map);
    }, 500);
}

// Add a listener to make an ES data request when the map bounds change
function add_bounds_changed_listener(map) {
    google.maps.event.addListenerOnce(map, 'bounds_changed', function () {
        redraw_map();
    });
}

// Start the main "bounds_changed" listener loop
window.onload = function () {
    // Draw histogram
    var resp = request_histogram();

    // Add listener to update mouse position
    // see: http://bit.ly/1zAfter
    google.maps.event.addListener(map, 'mousemove', function(event) {
        lat = event.latLng.lat().toFixed(4);
        lon = event.latLng.lng().toFixed(4);
		$("#mouse").html(lat + ', ' + lon);
	});


    // Centre the map on Hungary initially
    geocoder.geocode(
        {
            "address": "Lake Balaton, Hungary"
        },
        function (results, status) {
            if (status === "OK") {
                map.setCenter(results[0].geometry.location);
            }
        }
    );

    // Set up location 'search' button
    $("#location_search").click(
        function () {
            location_search();
        }
    );

    // Clears all input values
    $("#clearfil").click(
        function () {
            $("#ftext").val("");
            $("#start_time").val("");
            $("#end_time").val("");

            cleanup();
            redraw_map();
        }
    );

    // Constructs query filters from input values
    $("#applyfil").click(
        function () {
            cleanup();
            redraw_map();
        }
    );

    // Override location form submission on 'enter'
    $("#location").keypress(
        function (e) {
            var charcode = e.charCode || e.keyCode || e.which;
            if (charcode === 13) {
                location_search();
                return false;
            }
        }
    );

    add_bounds_changed_listener(map);
};
