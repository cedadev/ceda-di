// Constants
var es_url = "http://fatcat-test.jc.rl.ac.uk:9200/badc/eufar/_search";

// Initialise map
var map = new google.maps.Map(document.getElementById('map'), {
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    zoom: 6
});

// Array function
function is_in(array, item) {
    for (i = 0; i < array.length; i++) {
        if (i === array[i]) {
            return true;
        }
    }
    return false;
}

// Centre the map on Hungary (because there's lots of data there)
var address = "Lake Balaton, Hungary"
var geocoder = new google.maps.Geocoder();
geocoder.geocode(
    {
        "address": address
    },
    function(results, status) {
            map.setCenter(results[0].geometry.location);
    }
);

// Creates an ES geo_shape filter query based on a bounding box
function create_es_request(bbox, offset) {
    temp_ne = bbox.getNorthEast();
    temp_sw = bbox.getSouthWest();

    // Build search extent using lng/lat and opposite corners
    nw = [temp_sw.lng().toString(),
          temp_ne.lat().toString()];
    se = [temp_ne.lng().toString(),
          temp_sw.lat().toString()];

    // Construct request for ElasticSearch
    request = {
        "_source": {
            "include": [
                "file.filename",
                "file.path",
                "spatial.geometries.bbox",
                "temporal"
            ]
        },
        "query": {
            "geo_shape": {
                "bbox": {
                    "shape": {
                        "type": "envelope",
                        "coordinates": [nw, se]
                    }
                }
            }
        },
        "size": 15
    };

    return request;
};

// Construct a google.maps.Polygon object from a bounding box
function construct_polygon(bbox) {
    // Construct bounding box polygon
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

// Construct an info window from an ElasticSearch hit
// containing some useful metadata
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
               hit.file.path + "\">Get data</a></p></section>"

    info = new google.maps.InfoWindow({
        content: content
    });

    return info;
}

// Search ES for data (and display received data asynchronously)
var polygons = []
var info_windows = []
function search_es_bbox(bbox) {
    xhr = new XMLHttpRequest();
    xhr.open("POST", es_url, true);
    xhr.send(JSON.stringify(create_es_request(bbox)));

    // Handle the response
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            response = JSON.parse(xhr.responseText);
            if (response.hits) {
                hits = response.hits.hits;
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

                // Add a listener to the constructed Polygon that closes all
                // InfoWindows, then opens a new one corresponding to the
                // polygon that was clicked
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
        }
    }
}

// Add a listener to make an ES data request when the map bounds change
function add_bounds_changed_listener(map) {
    google.maps.event.addListenerOnce(map, 'bounds_changed',
        function() {
            // Clean up old polygons and info windows
            for (p in polygons) {
                polygons[p].setMap(null);
            }

            for (i in info_windows) {
                info_windows[i].close();
            }

            polygons = [];
            info_windows = []

            // Make ES request
            bounds = map.getBounds();
            search_es_bbox(bounds);

            // Rate-limit requests to ES to 1 per second
            window.setTimeout(function () {
                add_bounds_changed_listener(map)
            }, 1000);
        }
    );
}

// Start the main "bounds_changed" listener loop
add_bounds_changed_listener(map);
