/*jslint browser: true, devel: true, sloppy: true*/
/*global google, $*/

// Window constants
var wps_url = "http://ceda-wps2.badc.rl.ac.uk:8080/submit/form?proc_id=PlotTimeSeries&FilePath=";
var track_colours = ["#4D4D4D", "#5DA5DA", "#FAA43A",
                     "#60BD68", "#F17CB0", "#B2912F",
                     "#B276B2", "#DECF3F", "#F15854"];

// -----------------------------String.hashCode--------------------------------
String.prototype.hashCode = function () {
    // Please see: http://bit.ly/1dSyf18 for original
    var i, c, hash;

    hash = 0;
    if (this.length === 0) {
        return hash;
    }

    for (i = 0; i < this.length; i++) {
        c = this.charCodeAt(i);
        hash = ((hash << 5) - hash) + c;
    }

    return hash;
};

// -------------------------------ElasticSearch--------------------------------
var es_url = "http://fatcat-test.jc.rl.ac.uk:9200/badc/eufar/_search";
function request_from_filters(full_text) {
    var req;

    if (full_text.length > 0) {
        req = {
            "term": {
                "_all": full_text
            }
        };

        return req;
    }
}

function create_elasticsearch_request(gmaps_corners, full_text) {
    var tmp_ne, tmp_sw, nw, se, request, tf;

    tmp_ne = gmaps_corners.getNorthEast();
    tmp_sw = gmaps_corners.getSouthWest();
    nw = [tmp_sw.lng().toString(), tmp_ne.lat().toString()];
    se = [tmp_ne.lng().toString(), tmp_sw.lat().toString()];

    // ElasticSearch request
    request = {
        _source: {
            include: [
                "data_format.format",
                "file.filename",
                "file.path",
                "misc",
                "spatial.geometries.summary",
                "temporal"
            ]
        },
        filter: {
            and: {
                must: [
                    {
                        geo_shape: {
                            bbox: {
                                shape: {
                                    type: "envelope",
                                    coordinates: [nw, se]
                                }
                            }
                        }
                    }
                ]
            }
        },
        size: 100,
    };

    // Add extra filters from free-text search box
    tf = request_from_filters(full_text);
    if (tf) {
        request.filter.and.must.push(tf);
    }

    return request;
}

function send_elasticsearch_request(gmap, full_text) {
    var xhr, request, response;

    request = create_elasticsearch_request(gmap.getBounds(), full_text);

    // Construct and send XMLHttpRequest
    xhr = new XMLHttpRequest();
    xhr.open("POST", es_url, true);
    xhr.send(JSON.stringify(request));
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            response = JSON.parse(xhr.responseText);
            if (response.hits) {
                $("#resptime").html(response.took);
                $("#numresults").html(response.hits.total);

                draw_flight_tracks(gmap, response.hits.hits);
            }
        }
    };

}

// -----------------------------------Map--------------------------------------
var flight_tracks = [];
var info_windows = [];

function centre_map(gmap, geocoder, loc) {
    if (loc !== "") {
        geocoder.geocode({
            address: loc
        },
        function (results, status) {
            if (status === "OK") {
                gmap.panTo(results[0].geometry.location);
            } else {
                alert("Could not find \"" + loc + "\"");
            }
        });
    }
}

function create_info_window(hit) {
    var content, info;

    hit = hit._source;
    content = "<section><p><strong>Filename: </strong>" + hit.file.filename + "</p>";
    if (hit.temporal) {
        content += "<p><strong>Start Time: </strong>" + hit.temporal.start_time + "</p>" +
                    "<p><strong>End Time: </strong>" + hit.temporal.end_time + "</p>";
    }

    if (hit.misc.flight_num) {
        content += "<p><strong>Flight Num: </strong>\"" + hit.misc.flight_num + "\"</p>";
    }

    if (hit.misc.organisation) {
        content += "<p><strong>Organisation: </strong>\"" + hit.misc.organisation + "\"</p>";
    }

    content += "<p><a href=\"http://badc.nerc.ac.uk/browse" + hit.file.path + "\">Get data</a></p>";
    if (hit.data_format.format.search("RAF") > 0) {
        content += "<p><a href=\"" + wps_url + hit.file.path + "\" target=\"_blank\">Plot time-series</a></p>";
    }

    content += "</section>";
    info = new google.maps.InfoWindow(
        {
            content: content,
            disableAutoPan: false
        }
    );

    return info;
}

function draw_flight_tracks(gmap, hits) {
    var i, j, coords, corrected_coords, colour_index, track, hit, info_window;

    for (i = 0; i < hits.length; i+= 1) {
        hit = hits[i];

        // Construct flight track (flipping coordinates in the process)
        coords = hit._source.spatial.geometries.summary.coordinates;
        corrected_coords = [];
        for (j = 0; j < coords.length; j += 1) {
            corrected_coords.push(
                    new google.maps.LatLng(coords[j][1], coords[j][0]));
        }

        colour_index = (hit._id.hashCode() % track_colours.length);
        if (colour_index < 0) {
            colour_index = -colour_index;
        }

        if (corrected_coords.length > 1) {
            // Construct and display track
            track = new google.maps.Polyline({
                path: corrected_coords,
                geodesic: false,
                strokeColor: track_colours[colour_index],
                strokeWeight: 5,
                strokeOpacity: 0.6
            });
            track.setMap(gmap);
            flight_tracks.push(track);
        } else {
            marker = new google.maps.Marker({
                position: corrected_coords[0],
                icon: "./img/camera.png"
            });
            marker.setMap(gmap);
            flight_tracks.push(marker);
        }

        // Construct info window
        info_window = create_info_window(hit);

        // Add to lists
        info_windows.push(info_window);
    }

    for (i = 0; i < flight_tracks.length; i++) {
        google.maps.event.addListener(flight_tracks[i], 'click',
            (function (i, e) {
                return function (e) {
                    google.maps.event.clearListeners(gmap, "bounds_changed");

                    for (var j = 0; j < info_windows.length; j++) {
                        info_windows[j].close();
                    }

                    info_windows[i].setPosition(e.latLng);
                    info_windows[i].open(gmap, null);

                    window.setTimeout(function () {
                        add_bounds_changed_listener(gmap);
                    }, 500);
                };
            }
        )(i));
    }
}

function cleanup() {
    var i;

    for (i = 0; i < flight_tracks.length; i += 1) {
        flight_tracks[i].setMap(null);
    }
    flight_tracks = [];

    for (i = 0; i < info_windows.length; i += 1) {
        info_windows[i].close();
    }
    info_windows = [];
}

function redraw_map(gmap) {
    cleanup();

    // Draw flight tracks
    full_text = $("#ftext").val();
    send_elasticsearch_request(gmap, full_text);

    window.setTimeout(function () {
        add_bounds_changed_listener(gmap);
    }, 500);
}

function add_bounds_changed_listener(gmap) {
    google.maps.event.addListenerOnce(gmap, "bounds_changed", function () {
        redraw_map(gmap);
    });
}

// ------------------------------window.onload---------------------------------
window.onload = function () {
    var geocoder, lat, lon, map;

    // Google Maps geocoder and map object
    geocoder = new google.maps.Geocoder();
    map = new google.maps.Map(
        document.getElementById("map"),
        {
            mapTypeId: google.maps.MapTypeId.TERRAIN,
            zoom: 4
        }
    );

    centre_map(map, geocoder, "Lake Balaton, Hungary");
    google.maps.event.addListener(map, 'mousemove', function(event) {
        // Add listener to update mouse position
        // see: http://bit.ly/1zAfter
        lat = event.latLng.lat().toFixed(4);
        lon = event.latLng.lng().toFixed(4);
		$("#mouse").html(lat + ', ' + lon);
	});

    // Set up buttons
    $("#location_search").click(
        function () {
            centre_map(map, geocoder, $("#location").val());
        }
    );

    $("#location").keypress(
        function (e) {
            var charcode = e.charCode || e.keyCode || e.which;
            if (charcode === 13) {
                centre_map(map, geocoder, $("#location").val());
                return false;
            }
        }
    );

    $("#applyfil").click(
        function () {
            cleanup();
            redraw_map(map);
        }
    );

    $("#clearfil").click(
        function () {
            $("#ftext").val("");
            cleanup();
            redraw_map(map);
        }
    );

    $("#multiselect").multiSelect();

    add_bounds_changed_listener(map);
};
