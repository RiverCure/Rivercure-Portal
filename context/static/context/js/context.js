//Help functions
var MyFunctions = {
    deleting: false,
    //Layer for highlights
    highlightLayer: null,
    //Layer Group for sensor
    sensorsLayer: null,
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
    //Dictionary with the feature groups of the polygons to draw
    createdPolygons: {},
    //function to draw sensors on the map
    drawSensors: (map, sensors, iconUrl) => {
        MyFunctions.sensorsLayer = L.layerGroup();
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
    //function to init polygons
    polygonsInit: (map) => {
        MyFunctions.createdPolygons.Domain = L.layerGroup().addTo(map);
        MyFunctions.createdPolygons.Refinement = L.layerGroup().addTo(map);
        MyFunctions.createdPolygons.Alignment = L.layerGroup().addTo(map);

        MyFunctions.highlightLayer = L.featureGroup().addTo(map);

        map.layerscontrol.addOverlay(MyFunctions.createdPolygons.Domain, "Domain");
        map.layerscontrol.addOverlay(MyFunctions.createdPolygons.Refinement, "Refinement");
        map.layerscontrol.addOverlay(MyFunctions.createdPolygons.Alignment, "Alignment");
    },
    //funtion to init the boundaries variable
    boundariesInit: (map) => {
        MyFunctions.createdPolygons.Boundaries = L.layerGroup();
        map.addLayer(MyFunctions.createdPolygons.Boundaries);
        map.layerscontrol.addOverlay(MyFunctions.createdPolygons.Boundaries, 'Boundaries');
    },
    //function to return boundary line popup
    boundaryPopup: (type, dataType) => {
        
        getType = (option) => {
            switch(option){
                case 'Input':
                    return `<option id='popup-current-type' value="Input" selected>Input</option>
                            <option value="Output">Output</option>
                            <option value="InputOutput">Input Output</option>`
                case 'Output':
                    return `<option value="Input">Input</option>
                            <option id='popup-current-type' value="Output" selected>Output</option>
                            <option value="InputOutput">Input Output</option>`
                default:
                    return `<option value="Input">Input</option>
                            <option value="Output">Output</option>
                            <option id='popup-current-type' value="InputOutput" selected>Input Output</option>`
            }
        };

        getDataType = (option) => {
            switch(option){
                case 'H':
                    return `<option id='popup-current-data-type' value="H" selected>Depth</option>
                            <option value="Q">Discharge</option>
                            <option value="Z">Elevation</option>
                            <option value="V">Velocity</option>`
                case 'Q':
                    return `<option value="H">Depth</option>
                            <option id='popup-current-data-type' value="Q" selected>Discharge</option>
                            <option value="Z">Elevation</option>
                            <option value="V">Velocity</option>`
                case 'Z':
                    return `<option value="H">Depth</option>
                            <option value="Q">Discharge</option>
                            <option id='popup-current-data-type' value="Z" selected>Elevation</option>
                            <option value="Velocity">Velocity</option>`
                default:
                    return `<option value="H">Depth</option>
                            <option value="Q">Discharge</option>
                            <option value="Z">Elevation</option>
                            <option id='popup-current-data-type' value="V" selected>Velocity</option>`
            }
        };
        
        return `<h1><small>Boundary</small></h1>
            <div class="form-group">
                <label for="popup-selected-type"><big>Type</big></label><br>
                <select id='popup-selected-type' class="form-control form-control-sm">
                    ` + getType(type) + `
                </select>
            </div>
            <div class="form-group">
                <label for="popup-selected-data-type"><big>Data Type</big></label><br>  
                <select id='popup-selected-data-type' class="form-control form-control-sm">
                    ` + getDataType(dataType) + `
                </select>
                  
            </div>
            <button type="button" id='popup-btn' class="btn btn-outline-info btn-sm")">Save</button>
        `
    }, 
    //function to configure boundary popup
    boundaryLinePopupConfig: (popup) => {
        //define popup alteration saving
        popup.on('popupopen', e => { // function to handle the saving of the data
            setTimeout(() => { //wait in case user opens popups back to back
                //set the color of the current choice
                document.querySelector('#popup-current-type').style.backgroundColor = 'lightblue';
                document.querySelector('#popup-current-data-type').style.backgroundColor = 'lightblue';
                document.querySelector('#popup-btn').addEventListener('click', () => {
                    e.popup.setContent(MyFunctions.boundaryPopup(document.querySelector('#popup-selected-type').value, document.querySelector('#popup-selected-data-type').value));
                    e.popup.update();
                    setTimeout(() => { e.target.closePopup();}, 1500);
                });
            }, 1000);
        });
    },
    //function to return polygons CL popups
    polygonsPopup: (name, CL) => {
        return `
            <h1><small id='popup-header'>` + name + `</small></h1>
            <table class='table'>
                <tr>
                    <th scope="row">Current CL</th>
                    <td id='popup-current-cl'>`+ CL + `</td id='end-cl'>
                </tr>
                <tr>
                    <th scope="row">CL</th>
                    <td>
                        <input id='popup-selected-cl' type='number'>
                    </td>
                </tr>
            </table>
            <button type="button" id='popup-btn' class="btn btn-outline-info btn-sm")">Save</button>
        `
    },
    //function to configure polygon popup
    polygonsPopupConfig: (popup) => {
        popup.on('popupopen', e => { //define popup alteration saving
            if(!MyFunctions.deleting) {
                setTimeout(() => { //wait in case user opens popups back to back
                    document.querySelector('#popup-btn').addEventListener('click', () => {
                        e.popup.setContent(MyFunctions.polygonsPopup(document.querySelector('#popup-header').innerHTML, document.querySelector('#popup-selected-cl').value));
                        e.popup.update();
                        setTimeout(() => { e.target.closePopup();}, 1500);
                    });
                }, 1000);
            }
        });
    },
    //function to set the domain markers layers visibility toggle
    setDomainMarkers: (map) => {
        MyFunctions.domainMarkers = L.markerClusterGroup();
        MyFunctions.domainMarkers.addTo(map);
        map.layerscontrol.addOverlay(MyFunctions.domainMarkers, "Domain markers");

        //add a popup to select a sensor to associate
        MyFunctions.domainMarkers.bindPopup(`
            <h1><small>Water entry point</small></h1>
            <label for="sensor-association">Choose a sensor:</label>
            <input type="text" id="sensor-association" name="sensor-association">
        `);
        MyFunctions.domainMarkers.bindTooltip("Pick boundary and click me!");

        MyFunctions.domainMarkers.on('popupopen', e => {
            if(document.querySelector("#polygon-type").value === 'Boundary') {
                e.target.closePopup();
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
    polygonTypeChange: (e, drawControl) => {
        switch(e.target.value) {
            case "none":
                alert("Please select a polygon type");
                break;
            case "Domain":
                MyFunctions.enablePolygon(drawControl, '#C0C0C0', true);
                break;
            case "Boundary":
                if(MyFunctions.createdPolygons.Domain.getLayers().length === 0) { //Domain is not defined therefore disallow user from drawing the boundary
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
        // let coordinates = MyFunctions.drawnPolygn._layers[MyFunctions.createdPolygons.Domain]._latlngs[0];
        let coordinates = MyFunctions.createdPolygons.Domain.getLayers()[0].getLatLngs()[0];
        // for(let i = 0; i < coordinates.length; i++) //populate the vertices with markers again
        //     MyFunctions.addDomainMarker(map, coordinates[i].lat, coordinates[i].lng);
        for(coordinate of coordinates) {//populate the vertices with markers again
            MyFunctions.addDomainMarker(map, coordinate.lat, coordinate.lng);
        }
    },
    //function to delete layers from created polygons when deleting from drawnpolygn
    removeLayers: (layers) => {
        for(layer of layers) {
            MyFunctions.createdPolygons.Domain.removeLayer(layer);
            MyFunctions.createdPolygons.Refinement.removeLayer(layer);
            MyFunctions.createdPolygons.Alignment.removeLayer(layer);
        }
    },
    //function to remove domain markers
    clearLayers: () => {
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.createdPolygons.Boundaries.clearLayers();
    },
    //function to add domain marker
    addDomainMarker: (map, lat, lng) => {
        let marker = L.marker([lat, lng]).addTo(MyFunctions.domainMarkers);

        //add the logic to draw the boundary based on the domain polygon vertex
        marker.on('click', e => {
            console.log(e);
            if(document.querySelector("#polygon-type").value === 'Boundary') {
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
                MyFunctions.defineBoundary(MyFunctions.boundaryPolyline, null, null);
            }
            MyFunctions.tempPolyline.setLatLngs([]); //remove visual aid since the polyline draw is finished
            MyFunctions.boundaryPolyline = null; //restart the boundary draw
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
            case "Domain":
                if(MyFunctions.createdPolygons.Domain.getLayers().length >= 1) { // allow only 1 domain
                    alert('You can only draw 1 domain!');
                    document.querySelector('a[title="Cancel drawing"]').click();            
                }
            default:
                if(e.layerType === "polyline") {
                    alert("Invalid shape for selected polygon");
                    //stop drawing
                    document.querySelector('a[title="Cancel drawing"]').click();            
                }
        }
    },
    //function to send the polygons to the web server
    sendContext: () => {
        //prepare the visualization of the operation result
        try {
            let popup;
            // Save the polygons in geojsons and then serialize them to send to the web server
            var domain = MyFunctions.createdPolygons.Domain.getLayers()[0].toGeoJSON();
            popup = MyFunctions.createdPolygons.Domain.getLayers()[0].getPopup().getContent();
            domain.properties.CL = popup.slice(popup.indexOf('current-cl\'>') + 'current-cl\'>'.length, popup.indexOf('</td id=\'end-cl')).trim();

            var alignment = {"type": "FeatureCollection", "features": []}; //save all the alignment geometries
            MyFunctions.createdPolygons.Alignment.getLayers().forEach((element) => {
                alignmentUnit = element.toGeoJSON();
                popup = element.getPopup().getContent(); //get the popup to extract the properties values
                alignmentUnit.properties.CL = popup.slice(popup.indexOf('current-cl\'>') + 'current-cl\'>'.length, popup.indexOf('</td id=\'end-cl')).trim();
                alignment.features.push(alignmentUnit);
            });

            var refinement = {"type": "FeatureCollection", "features": []}; //save all the refinement geometries
            MyFunctions.createdPolygons.Refinement.getLayers().forEach((element) => {
                refinementUnit = element.toGeoJSON();
                popup = element.getPopup().getContent(); //get the popup to extract the properties values
                refinementUnit.properties.CL = popup.slice(popup.indexOf('current-cl\'>') + 'current-cl\'>'.length, popup.indexOf('</td id=\'end-cl')).trim();
                refinement.features.push(refinementUnit);
            });

            // Fill the hidden form fields with the values
            document.querySelector('#id_domain').value = JSON.stringify(domain);
            document.querySelector('#id_alignment').value = JSON.stringify(alignment);
            document.querySelector('#id_refinement').value = JSON.stringify(refinement);
            //Handle the boundaries
            var boundaries = {"type": "FeatureCollection", "features": []};
            MyFunctions.createdPolygons.Boundaries.getLayers().forEach((element) => {
                boundaryLine = element.toGeoJSON();
                popup = element.getPopup().getContent(); //get the popup to extract the properties values
                boundaryLine.properties.type = popup.slice(popup.indexOf('current-type\' value="') + 'current-type\' value="'.length, popup.indexOf('" selected')).trim();
                boundaryLine.properties.dataType = popup.substr(popup.indexOf('data-type\' value="') + 'data-type\' value="'.length, 1).trim();
                boundaries.features.push(boundaryLine);
            });
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
        MyFunctions.createdPolygons.Boundaries.clearLayers();
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.drawnPolygn.clearLayers();

        for(key in MyFunctions.createdPolygons)
            MyFunctions.createdPolygons[key].clearLayers();
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
            let domain = L.polygon(MyFunctions.coordStringToArray(response.geomExternalBoundary), {color: '#C0C0C0'});
            MyFunctions.definePolygon(domain, "Domain", response.CLExternalBoundary);
            MyFunctions.editStop(map); //draw the markers
        }
        //Refinement
        if(response.context_refinement !== null && response.context_refinement.length > 0) {
            let refinement;
            response.context_refinement.forEach((element) => {
                refinement = L.polygon(MyFunctions.coordStringToArray(element.geom), {color: '#FFA500'})
                MyFunctions.definePolygon(refinement, "Refinement", element.CL);
            });
        }
        //Alignment
        if(response.context_alignment !== null && response.context_alignment.length > 0) {
            let alignment;
            response.context_alignment.forEach((element) => {
                alignment = L.polyline(MyFunctions.coordStringToArray(element.geom), {color: '#FFFF00'});
                MyFunctions.definePolygon(alignment, "Alignment", element.CL);
            });
        }
        //Boundaries
        if(response.context_boundaries !== null && response.context_boundaries.length > 0) {
            let boundary;
            response.context_boundaries.forEach((element) => { //define each boundary line individually
                boundary = L.polyline(MyFunctions.coordStringToArray(element.geom));
                MyFunctions.defineBoundary(boundary, element.type, element.dataType);
            });
        }
    },
    //function to define polygons on all necessary layers
    definePolygon: (layer, type, CL) => {
        var polygonLayer;
        switch(type) { //get the proper storing structure             
            case "Domain":
                polygonLayer = MyFunctions.createdPolygons.Domain;
                break;
            case "Alignment":
                polygonLayer = MyFunctions.createdPolygons.Alignment;
                break;
            case "Refinement":
                polygonLayer = MyFunctions.createdPolygons.Refinement;
                break;
        }

        MyFunctions.polygonsPopupConfig(layer.bindPopup(MyFunctions.polygonsPopup(type, CL)));
        layer.bindTooltip(type);
        polygonLayer.addLayer(layer); //Domain
        MyFunctions.drawnPolygn.addLayer(layer); //Add to this layer for editing

        // layer.on('mouseover', e => {
        //     console.log(e);
        //     console.log('in')
        //     MyFunctions.highlightLayer.addLayer(L.geoJson(polygonLayer.getLayer(e.target._leaflet_id).toGeoJSON()))
        //     .on('mouseout', () => {
        //         console.log('out');
        //         MyFunctions.highlightLayer.clearLayers();
        //     });
        // });
    },
    //function to define boundary and draw it on the map
    defineBoundary: (boundary, type, dataType) => {
        MyFunctions.createdPolygons.Boundaries.addLayer(boundary);
        MyFunctions.boundaryLinePopupConfig(boundary.bindPopup(MyFunctions.boundaryPopup(type, dataType)));
        boundary.bindTooltip("Boundary");
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