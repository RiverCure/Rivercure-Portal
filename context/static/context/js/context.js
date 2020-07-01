//Help functions
var MyFunctions = {
    // //Polygns to store
    // Domain: null,
    // Boundary: null,
    // Alignment: null,
    // Refinement: null,
    //Variable to store boundary polyline being drawn
    boundaryPolyline: null,
    //Variable to store the drawn boundaries
    boundaries: [],
    //variable to store a temp polyline to serve as a visual aid to the user
    tempPolyline: L.polyline([], {color: '#0000A0', opacity: 0.2}),
    //Geojson structure to send to the server with the defined geometries
    geojson: {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Name": "Domain"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": []
                }
            },
            {
                "type": "Feature",
                "properties": {"Name": "Refinement"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": []
                }
            },
            {
                "type": "Feature",
                "properties": {"Name": "Alignment"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": []
                }
            },
            {
                "type": "Feature",
                "properties": {"Name": "Boundary"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": []
                }
            }
        ]
    },
    //function to configure draw control
    drawControlConfig: (drawnPolygn) => {
        return new L.Control.Draw({
            //leave only polygon option in the control
            draw: { 
                marker: false,
                circlemarker: false,
                rectangle: false,
                circle: false,
                polygon: {
                    shapeOptions: {
                        fill: false
                    }
                },
                polyline: {
                    allowIntersection: false,
                },
            },
            edit: {
                featureGroup: drawnPolygn,
                allowIntersection: false,
            }
        });
    },
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
    //enable controls when users changes the select polygon
    polygonTypeChange: (e, drawControl, domain) => {
        switch(e.target.value) {
            case "none":
                alert("Please select a polygon type");
                break;
            case "Domain":
                MyFunctions.enablePolygon(drawControl, '#C0C0C0', true);
                break;
            case "Boundary":
                if(domain != null) MyFunctions.enablePolyline(drawControl, '#0000A0'); //if domain is already defined then allow the drawing of the boundary
                else { //Domain is not defined therefore disallow user from drawing the boundary
                    alert("Define the Domain before defining the boundaries");
                    e.target.selectedIndex = "0";
                }
                break;
            case "Alignment":
                MyFunctions.enablePolyline(drawControl, '#FFFF00');
                break;
            case "Refinement":
                MyFunctions.enablePolygon(drawControl, '#FFA500', true);
                break;
        }
    },
    //function to hadle the showing of mouse position
    showMousePosition: (map) => {
        latlngDiv = document.createElement("div");
        latlngDiv.setAttribute("class", "leaflet-control-scale");
        latlngDivContent = document.createElement("div");
        latlngDiv.setAttribute("id", "mouse-latlng");
        latlngDiv.append(latlngDivContent);

        document.querySelector(".leaflet-bottom.leaflet-bottom").append(latlngDiv);                
    },
    mouseMove: (map) => {
        MyFunctions.tempPolyline.addTo(map);
        //add the listener to update the values
        map.addEventListener('mousemove', e => {
            //update the lat and lng values of the div added on showMousePosition()
            document.querySelector("#mouse-latlng").innerHTML = "Lat: " + e.latlng.lat.toFixed(5)+ " Lon: " + e.latlng.lng.toFixed(5); 

            if(document.querySelector("#polygon-type").value == 'Boundary' && MyFunctions.boundaryPolyline != null) { //if the user is drawing the boundary
                let aux = MyFunctions.boundaryPolyline.getLatLngs();
                aux = aux[aux.length - 1];
                //draw a polyline from the last point clicked to the mouse position
                MyFunctions.tempPolyline.setLatLngs([aux, [e.latlng.lat, e.latlng.lng]]);
            }
        });
    },
    //function to add markers when drawing the boundary
    vertexAdded: (e, map, domain) => {
        let polygonType = document.querySelector("#polygon-type").value;
        let lat = Object.values(e.layers._layers)[Object.values(e.layers._layers).length - 1]._latlng.lat;
        let lng = Object.values(e.layers._layers)[Object.values(e.layers._layers).length - 1]._latlng.lng;
        if(polygonType == 'Domain') { //if we're drawing the domain then
            //mark the vertex with a marker
            let marker = L.marker([lat, lng]).addTo(map);
            marker.bindPopup(`
                <h1><small>Water entry point</small></h1>
                <label for="water-entry-type">Choose a type:</label>
                <select name="water-entry-type">
                    <option value="h">H</option>
                    <option value="q">Q</option>
                </select>
            `);
            marker.bindTooltip("Pick boundary and click me!");
            //add the logic to draw the boundary based on the domain polygon vertex
            marker.on('click', () => {
                if(document.querySelector("#polygon-type").value == 'Boundary') {
                    marker.closePopup(); //close the popup that opens automatically
                    if(MyFunctions.boundaryPolyline == null) { //if it's the first point of the polyline being added to the map then
                        MyFunctions.boundaryPolyline = L.polyline([[lat,lng]], color='#0000A0').addTo(map);
                    }
                    else { //if there are already defined points then draw the polyline
                        //add some logic to guarantee that the points are sequential in the array
                        MyFunctions.boundaryPolyline.addLatLng([lat, lng]);
                        MyFunctions.tempPolyline.setLatLngs([[lat, lng], MyFunctions.tempPolyline.getLatLngs()[1]]);
                    }
                }
            });
            //console.log(domain.getBounds());
        }
    },
    //function when the user clicks on the map (to stop the boundary line)
    mapClick: (e, map) => {
        if(document.querySelector("#polygon-type").value == 'Boundary') { //this function is only used when the user is drawing the boundary
            if(MyFunctions.boundaryPolyline != null) { //check if the user is currently drawing the boundary
                MyFunctions.boundaries.push(MyFunctions.boundaryPolyline); //store the previously drawn boundary
                MyFunctions.boundaryPolyline = null; //restart the boundary draw
                MyFunctions.tempPolyline.setLatLngs([]); //remove visual aid since the polyline draw is finished
            }
        }
    },
    //function to run on the begginning of a drawing
    drawStart: (e) => {
        let polygonType = document.querySelector("#polygon-type"); //select the dropdown element of the polygon type
        polygonType.disabled = true; //disable the selection of the polygon type again

        switch(polygonType.value) {
            case "none":
                alert("Please select a polygon type");
                //stop drawing
                document.querySelector('a[title="Cancel drawing"]').click();       
                break;
            case "Alignment":
                if(e.layerType == "polygon") {
                    alert("Invalid shape for selected polygon");
                    //stop drawing
                    document.querySelector('a[title="Cancel drawing"]').click();       
                }
                break;
            case "Boundary":
                alert("Invalid shape for selected polygon\nClick on the domain markers to draw the boundary");
                //stop drawing
                document.querySelector('a[title="Cancel drawing"]').click();       
                break;
            default:
                if(e.layerType == "polyline") {
                    alert("Invalid shape for selected polygon");
                    //stop drawing
                    document.querySelector('a[title="Cancel drawing"]').click();            
                }
        }
    },
    //function to run when draw is created
    drawCreated: (e, createdPolygons) => {
        drawnPolygn.addLayer(e.layer);
        let polygonType = document.querySelector("#polygon-type").value;
        // console.log(e.layer._bounds.contains([38.707616,-9.1365]));
        // console.log(e.layer.getBounds());
        //save the polygon in the appropriate variable
        switch(polygonType) {                    
            case "Domain":
                createdPolygons.Domain = e.layer;
                break;
            case "Boundary":
                createdPolygons.Boundary = e.layer;
                break;
            case "Alignment":
                createdPolygons.Alignment = e.layer;
                break;
            case "Refinement":
                createdPolygons.Refinement = e.layer;
                break;
        }
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