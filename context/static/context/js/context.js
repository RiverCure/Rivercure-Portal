//Help functions
var MyFunctions = {
    //Layer Group for sensor
    sensorsLayer: L.layerGroup(),
    //Variable to store the features for editing
    drawnPolygn: null,
    //Variable to store boundary polyline being drawn
    boundaryPolyline: null,
    boundaryPolylineMarkersTemp: null,
    //variable to store a temp polyline to serve as a visual aid to the user
    tempPolyline: L.polyline([], {color: '#0000A0', opacity: 0.2}),
    //variable to store the domain markers
    domainMarkers: null,
    //vars with created polygons
    boundaries: null,
    //variable to store the boundary markers in the same order as the domain
    boundaryPolylineMarkers: [],
    createdPolygons: {"Domain": null, "Refinement": null, "Alignment": null},
    //function to draw sensors on the map
    drawSensors: (map, sensors, iconUrl) => {
        //icon for sensors
        let sensorIcon = L.icon( {iconUrl: iconUrl, iconSize: [50, 50]});
        let sensorMarker; //auxiliar variable
        for(sensor of sensors) {
            sensorMarker = L.marker(MyFunctions.coordStringToArray(sensor.geom)[0], {icon: sensorIcon}).addTo(MyFunctions.sensorsLayer);
            sensorMarker.bindPopup(`
                <table class='table'>
                    <tr>
                        <th scope="row">Code</th>
                        <td>` + sensor.code + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Name</th>
                        <td>` + sensor.name + `</td>
                    </tr>
                    <tr>
                        <th scope="row">ModalityType</th>
                        <td>` + sensor.modalityType + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Type</th>
                        <td>` + sensor.type + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Description</th>
                        <td>` + sensor.description + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Version</th>
                        <td>` + sensor.version + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Time Zone</th>
                        <td>` + sensor.timeZoneAbbreviation + `</td>
                    </tr>
                    <tr>
                        <th scope="row">Time Zone offset</th>
                        <td>` + sensor.timeZoneOffset + `</td>
                    </tr>
                </table>
            `);
        }
        MyFunctions.sensorsLayer.addTo(map);
        map.layerscontrol.addOverlay(MyFunctions.sensorsLayer, 'Sensors');
    },
    //function to configure draw control
    drawControlConfig: (map) => {
        MyFunctions.drawnPolygn = new L.FeatureGroup();
        map.addLayer(MyFunctions.drawnPolygn);
        
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
                featureGroup: MyFunctions.drawnPolygn,
                allowIntersection: false,
            }
        });
    },
    //funtion to init the boundaries variable
    boundariesInit: (map) => {
        MyFunctions.boundaries = L.featureGroup();
        map.addLayer(MyFunctions.boundaries);
        map.layerscontrol.addOverlay(MyFunctions.boundaries, 'Boundaries');

        //add a popup to select CONTEXTBOUNDARYLINEDATAKIND_CHOICES present in the model
        MyFunctions.boundaries.bindPopup(`
            <h1><small>Boundary</small></h1>
            <label for="water-entry-type">Choose a type:</label>
            <select name="water-entry-type">
                <option value="Depth">H</option>
                <option value="Discharge">Q</option>
                <option value="Elevation">Z</option>
                <option value="Velocity">V</option>
            </select> <br>
            <label for="water-entry-type">Choose a data type:</label>
            <select name="water-entry-type">
                <option value="Input">Input</option>
                <option value="Output">Output</option>
                <option value="InputOutput">Input Output</option>
            </select> <br>
            <button type="button" onclick="MyFunctions.saveBoundaryProperties(this)">Save</button>
        `);

        MyFunctions.boundaries.bindTooltip("Click to define variables");
    },
    //functions to save the boundary line variables
    saveBoundaryProperties: (e) => {
        console.log(e);

    },
    //function to set the domain markers layers visibility toggle
    setDomainMarkers: (map) => {
        MyFunctions.domainMarkers = L.featureGroup();
        MyFunctions.domainMarkers.addTo(map);
        map.layerscontrol.addOverlay(MyFunctions.domainMarkers, "Domain markers");

        //add a popup to select a sensor to associate
        MyFunctions.domainMarkers.bindPopup(`
            <h1><small>Water entry point</small></h1>
            <label for="sensor-association">Choose a sensor:</label>
            <input type="text" id="sensor-association" name="sensor-association">
        `);
        MyFunctions.domainMarkers.bindTooltip("Pick boundary and click me!");
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
    polygonTypeChange: (e, drawControl) => {
        switch(e.target.value) {
            case "none":
                alert("Please select a polygon type");
                break;
            case "Domain":
                MyFunctions.enablePolygon(drawControl, '#C0C0C0', true);
                break;
            case "Boundary":
                if(MyFunctions.createdPolygons.Domain === null) { //Domain is not defined therefore disallow user from drawing the boundary
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
    showMousePosition: () => {
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

            if(document.querySelector("#polygon-type").value === 'Boundary' && MyFunctions.boundaryPolyline != null) { //if the user is drawing the boundary
                let aux = MyFunctions.boundaryPolyline.getLatLngs();
                aux = aux[aux.length - 1];
                //draw a polyline from the last point clicked to the mouse position
                MyFunctions.tempPolyline.setLatLngs([aux, [e.latlng.lat, e.latlng.lng]]);
            }
        });
    },
    //function to add markers when drawing the boundary
    vertexAdded: (e, map) => {
        let polygonType = document.querySelector("#polygon-type").value;
        let lat = Object.values(e.layers._layers)[Object.values(e.layers._layers).length - 1]._latlng.lat;
        let lng = Object.values(e.layers._layers)[Object.values(e.layers._layers).length - 1]._latlng.lng;
        if(polygonType === 'Domain') { //if we're drawing the domain then
            //mark the vertex with a marker
            MyFunctions.addDomainMarker(map, lat, lng);
            //console.log(domain.getBounds());
        }
    },
    //function to redraw the domain markers when the edit stops
    editStop: (map) => {
        let coordinates = MyFunctions.drawnPolygn._layers[MyFunctions.createdPolygons.Domain]._latlngs[0];
        for(let i = 0; i < coordinates.length; i++) //populate the vertices with markers again
            MyFunctions.addDomainMarker(map, coordinates[i].lat, coordinates[i].lng);
    },
    //function to remove domain markers
    removeDomainMarkers: () => {
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.boundaries.clearLayers();
    },
    //function to add domain marker
    addDomainMarker: (map, lat, lng) => {
        let marker = L.marker([lat, lng]).addTo(MyFunctions.domainMarkers);

        //add the logic to draw the boundary based on the domain polygon vertex
        marker.on('click', e => {
            marker.openPopup()
            console.log(e);
            if(document.querySelector("#polygon-type").value === 'Boundary') {
                console.log('reeee');
                marker.closePopup(); //close the popup that opens automatically
                if(MyFunctions.boundaryPolyline === null) { //if it's the first point of the polyline being added to the map then
                    MyFunctions.boundaryPolyline = L.polyline([[lat,lng]], color='#0000A0').addTo(map);
                    //start saving the markers
                    MyFunctions.boundaryPolylineMarkersTemp = []; 
                    MyFunctions.boundaryPolylineMarkersTemp.push(marker);
                }
                else { //if there are already defined points then draw the polyline
                    //add some logic to guarantee that the points are sequential in the array
                    MyFunctions.boundaryPolyline.addLatLng([lat, lng]);
                    MyFunctions.tempPolyline.setLatLngs([[lat, lng], MyFunctions.tempPolyline.getLatLngs()[1]]);
                    MyFunctions.boundaryPolylineMarkersTemp.push(marker); //save the marker
                }
            }
        });
        marker.on('dblclick', () => { //remove the marker on double click
            marker.remove();
        });
        
    },
    //function when the user clicks on the map (to stop the boundary line)
    stopBoundaryDefinition: () => {
        if(document.querySelector("#polygon-type").value === 'Boundary') { //this function is only used when the user is drawing the boundary
            if(MyFunctions.boundaryPolyline != null && MyFunctions.boundaryPolylineMarkersTemp.length > 1) { //check if the user is currently drawing the boundary
                MyFunctions.boundaries.addLayer(MyFunctions.boundaryPolyline); //store the previously drawn boundary
                MyFunctions.boundaryPolylineMarkers.push(MyFunctions.boundaryPolylineMarkersTemp); //store the drawn markers
                MyFunctions.boundaryPolyline = null; //restart the boundary draw
            }
            MyFunctions.tempPolyline.setLatLngs([]); //remove visual aid since the polyline draw is finished
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
                if(e.layerType === "polygon") {
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
                if(e.layerType === "polyline") {
                    alert("Invalid shape for selected polygon");
                    //stop drawing
                    document.querySelector('a[title="Cancel drawing"]').click();            
                }
        }
    },
    //function to run when draw is created
    drawCreated: (e, map) => {
        MyFunctions.drawnPolygn.addLayer(e.layer);
        let polygonKey = Object.keys(MyFunctions.drawnPolygn._layers)[Object.keys(MyFunctions.drawnPolygn._layers).length - 1] //mapping to the object key which will contain the polygon
        let polygonType = document.querySelector("#polygon-type").value;
        //save the polygon in the appropriate variable
        switch(polygonType) {                    
            case "Domain":
                MyFunctions.createdPolygons.Domain = polygonKey;
                map.layerscontrol.addOverlay(e.layer, "Domain");
                break;
            case "Alignment":
                MyFunctions.createdPolygons.Alignment = polygonKey;
                map.layerscontrol.addOverlay(e.layer, "Alignment");
                break;
            case "Refinement":
                MyFunctions.createdPolygons.Refinement = polygonKey;
                map.layerscontrol.addOverlay(e.layer, "Refinement");
                break;
        }
    },
    //function to send the polygons to the web server
    sendContext: () => {
        //prepare the visualization of the operation result
        try {
            // Save the polygons in geojsons and then serialize them to send to the web server
            var domain = JSON.stringify(MyFunctions.drawnPolygn._layers[MyFunctions.createdPolygons.Domain].toGeoJSON());
            var alignment = JSON.stringify(MyFunctions.drawnPolygn._layers[MyFunctions.createdPolygons.Alignment].toGeoJSON());
            var refinement = JSON.stringify(MyFunctions.drawnPolygn._layers[MyFunctions.createdPolygons.Refinement].toGeoJSON());

            // Fill the hidden form fields with the values
            document.querySelector('#id_domain').value = domain;
            document.querySelector('#id_alignment').value = alignment;
            document.querySelector('#id_refinement').value = refinement;
            //Handle the boundaries
            var boundaries = {"type": "FeatureCollection", "features": []};
            MyFunctions.boundaries.getLayers().forEach((element, index) => {
                boundaryLine = element.toGeoJSON();
                // MyFunctions.boundaryPolylineMarkers[index].forEach((marker) => {
                //     console.log(marker.getPopup().getContent());
                // });
                // boundaryLine.properties['markers'] = MyFunctions.boundaryPolylineMarkers[index];
                boundaries.features.push(boundaryLine);
            });
            console.log(boundaries);
            document.querySelector('#id_boundaries').value = JSON.stringify(boundaries);
            
            // Change alert on form
            document.querySelector('#load-status').innerHTML = document.querySelector('#load-context-result').innerHTML = "Context Loaded";
            document.querySelector('#load-status').className = document.querySelector('#load-context-result').className = "alert alert-success";
        }
        catch(err) { //In case of invalid context
            console.log(err);
            document.querySelector('#load-context-result').setAttribute("class", "alert alert-danger");
            document.querySelector('#load-context-result').innerHTML = "Invalid Context";
        }
        finally {
            document.querySelector('#load-context-result').style.display = 'block';
        }
    },
    //function to get a context to edit
    getContext: (url, map) => {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", url, false); 
        xmlHttp.send(null);
        response = JSON.parse(xmlHttp.responseText);

        //show the form
        document.querySelector('#form-data').style.display = 'block';
        console.log(response);

        MyFunctions.fillForm(response);
        MyFunctions.drawGeometries(response, map);
    },
    //function to clear the map to fill with new data
    clearMap: () => {
        MyFunctions.boundaries.clearLayers();
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.drawnPolygn.clearLayers();

        for(key in MyFunctions.createdPolygons)
            MyFunctions.createdPolygons[key] = null;
    },
    //function to fill the form when the context with the api is called
    fillForm: (response) => {
        document.querySelector('#id_code').value = response.code;
        document.querySelector('#id_name').value = response.Name;
        document.querySelector('#id_hydroFeature').value = response.hydroFeature;
        // document.querySelector('#id_CLExternalBoundary').value = response.CLExternalBoundary;
        // document.querySelector('#id_CLAlignment').value = response.CLAlignment;
        // document.querySelector('#id_CLInternalBoundary').value = response.CLInternalBoundary;
    },
    //function to draw the geometries in the context from API call
    drawGeometries: (response, map) => {
        //Domain
        if(response.geomExternalBoundary !== null) { //check if the refinement is defined in the database
            MyFunctions.drawnPolygn.addLayer(L.polygon(MyFunctions.coordStringToArray(response.geomExternalBoundary), {color: '#C0C0C0'})); //Domain
            map.layerscontrol.addOverlay(Object.values(MyFunctions.drawnPolygn._layers)[Object.values(MyFunctions.drawnPolygn._layers).length - 1], "Domain"); //add the possibility to hide the layer
            MyFunctions.createdPolygons.Domain = Object.keys(MyFunctions.drawnPolygn._layers)[Object.keys(MyFunctions.drawnPolygn._layers).length - 1];
            MyFunctions.editStop(map); //behave as if an edit was finished to draw the markers of the boundary
        }
        //Refinement
        if(response.geomExternalBoundary !== null) { //check if the refinement is defined in the database
            MyFunctions.drawnPolygn.addLayer(L.polygon(MyFunctions.coordStringToArray(response.geomInternalBoundary), {color: '#FFA500'})); //Refinement
            map.layerscontrol.addOverlay(Object.values(MyFunctions.drawnPolygn._layers)[Object.values(MyFunctions.drawnPolygn._layers).length - 1], "Refinement"); //add the possibility to hide the layer
            MyFunctions.createdPolygons.Refinement = Object.keys(MyFunctions.drawnPolygn._layers)[Object.keys(MyFunctions.drawnPolygn._layers).length - 1];
        }
        //Alignment
        if(response.geomAlignment !== null) { //check if the alignment is defined in the database
            MyFunctions.drawnPolygn.addLayer(L.polyline(MyFunctions.coordStringToArray(response.geomAlignment), {color: '#FFFF00'})); //Alignment
            map.layerscontrol.addOverlay(Object.values(MyFunctions.drawnPolygn._layers)[Object.values(MyFunctions.drawnPolygn._layers).length - 1], "Alignment"); //add the possibility to hide the layer
            MyFunctions.createdPolygons.Alignment = Object.keys(MyFunctions.drawnPolygn._layers)[Object.keys(MyFunctions.drawnPolygn._layers).length - 1];
        }
        //Boundaries
        if(response.context_boundaries !== null && response.context_boundaries.length > 0) {
            response.context_boundaries.forEach((element) => {
                MyFunctions.boundaries.addLayer(L.polyline(MyFunctions.coordStringToArray(element.geom)));
            });
        }
    },
    //function to transform coordinate string into an array
    coordStringToArray: (string) => {
        let coordinates = [];
        string = string.slice(string.lastIndexOf('(') + 1, string.indexOf(')')).split(',');
        for(coord of string)
            coordinates.push([Number(coord.trim().split(' ')[1]), Number(coord.trim().split(' ')[0])]);
        return coordinates;
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