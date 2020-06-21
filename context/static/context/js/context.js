//Help functions
var MyFunctions = {
    //function to enable polygon drawing and disable polyline
    enablePolygon: (drawControl, polyColor, fillOption) => {
        drawControl.setDrawingOptions({
            polygon: {
                shapeOptions: {
                    fill: fillOption,
                    color: polyColor
                }
            },
        });
    },
    //function to enable polyline drawing and disable polygon
    enablePolyline: (drawControl, polyColor) => {
        drawControl.setDrawingOptions({
            polyline: {
                allowIntersection: false,
                shapeOptions: {
                    color: polyColor,
                    noClip: true
                }
            },
        });
    },
    //function to hadle the showing of mouse position
    showMousePosition: (map) => {
        latlngDiv = document.createElement("div");
        latlngDiv.setAttribute("class", "leaflet-control-scale");
        latlngDivContent = document.createElement("div");
        latlngDiv.setAttribute("id", "mouse-latlng");
        latlngDiv.append(latlngDivContent);

        document.querySelector(".leaflet-bottom.leaflet-bottom").append(latlngDiv);
        
        //add the listener to update the values
        map.addEventListener('mousemove', e => {
            document.querySelector("#mouse-latlng").innerHTML = "Lat: " + e.latlng.lat.toFixed(5)+ " Lon: " + e.latlng.lng.toFixed(5);
        });
    },
}


//add layers
        //var satellite = L.gridLayer.googleMutant({type: 'roadmap'});
        /*var satellite = L.tileLayer('http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}').addTo(map);
        var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMaps</a> contributors'});

        var baseLayers = {
            "Satellite": satellite,
            "OpenStreetMaps": osm
        }
        L.control.layers(baseLayers).addTo(map);*/