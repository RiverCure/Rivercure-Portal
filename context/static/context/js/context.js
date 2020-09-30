//Help functions
var MyFunctions = {
    //variable to change popups depending on the user page
    mode: 'edit',
    deleting: false,
    //Variable to store sensors
    sensors: null,
    contextSensors: null,
    //Layer for highlights
    highlightLayer: null,
    highlightStatus: null,
    //boolean to check completeness
    complete: false,
    //Layer Group for sensor
    sensorsLayer: null,
    //Variable to store the features for editing
    editPolygonFeature: null,
    //Variable to store boundary polyline being drawn
    boundaryPolyline: null,
    boundaryPolylineMarkersTemp: null,
    //variable to store a temp polyline to serve as a visual aid to the user
    tempPolyline: L.polyline([], {color: '#0000A0', opacity: 0.2}),
    //variable to store the domain markers
    domainMarkers: null,
    //vars with created polygons
    boundaries: null,
    //var to associate domain points to boundaries
    domainMarkerToBoundary: null,
    //Dictionary with the feature groups of the polygons to draw
    createdPolygons: {},
    //layer for the dtm raster
    dtm: null,
    //function to define draw sensor icon
    sensorIcon: (code, fill) => {
        return `
            <svg>
                <rect id="` + 'sensor-' + code + `" rx="20" ry="20" style="fill:` + fill + `;"/>
                <text x="50%" y="50%" alignment-baseline="middle" text-anchor="middle">` + code + `</text>  
            </svg>
        `
    },
    //function to define sensor popup
    sensorPopup: (sensor) => {
        return `
            <h1>Sensor ` + sensor.code + `</h1>
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
        `
    },     
    //function to draw sensors on the map
    drawSensors: (map, sensors) => {
        MyFunctions.sensorsLayer = L.markerClusterGroup({showCoverageOnHover: false});
        //icon for sensors
        let sensorIcon;
        let sensorMarker; //auxiliar variable
        MyFunctions.sensors = sensors;
        MyFunctions.contextSensors = {};
        for(sensor of sensors) {
            sensorIcon = L.divIcon({html: MyFunctions.sensorIcon(sensor.code, 'whitesmoke'), className: 'sensor', iconSize: [35, 35]});
            sensorMarker = L.marker(MyFunctions.coordStringToArray(sensor.geom)[0], {icon: sensorIcon}).addTo(MyFunctions.sensorsLayer);
            sensorMarker.bindPopup(MyFunctions.sensorPopup(sensor));
            sensorMarker.bindTooltip('Sensor ' + sensor.code);
            MyFunctions.contextSensors[sensor.code] = sensorMarker;
        }
        MyFunctions.sensorsLayer.addTo(map);
        map.layerscontrol.addOverlay(MyFunctions.sensorsLayer, 'Sensors');
    },
    //function to configure draw control
    drawControlConfig: (map) => {
        MyFunctions.editPolygonFeature = new L.FeatureGroup();
        map.addLayer(MyFunctions.editPolygonFeature);
        
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
                    },
                    allowIntersection: false,
                },
                polyline: {
                    allowIntersection: false,
                },
            },
            edit: {
                featureGroup: MyFunctions.editPolygonFeature,
                allowIntersection: false,
            }
        });
    },
    //function to init polygons
    polygonsInit: (map) => {
        MyFunctions.createdPolygons.Domain = L.layerGroup().addTo(map);
        MyFunctions.createdPolygons.Refinement = L.layerGroup().addTo(map);
        MyFunctions.createdPolygons.Alignment = L.layerGroup().addTo(map);
        MyFunctions.dtm = L.layerGroup().addTo(map);

        MyFunctions.domainMarkerToBoundary = {};
        MyFunctions.highlightLayer = L.featureGroup().addTo(map);

        map.layerscontrol.addOverlay(MyFunctions.dtm, 'DTM');
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
    boundaryPopup: (id, type, dataType) => {
        getType = () => {
            switch(type){
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

        getDataType = () => {
            switch(dataType){
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
        
        if(MyFunctions.mode == 'edit') {
            return `<h1><small>Boundary ` + id + `</small></h1>
                <div class="form-group">
                    <label for="popup-selected-type"><big>Type</big></label><br>
                    <select id='popup-selected-type' class="form-control form-control-sm">
                        ` + getType() + `
                    </select>
                </div>
                <div class="form-group">
                    <label for="popup-selected-data-type"><big>Data Type</big></label><br>  
                    <select id='popup-selected-data-type' class="form-control form-control-sm">
                        ` + getDataType() + `
                    </select>
                    
                </div>
                <button type="button" id='popup-btn' class="btn btn-outline-info btn-sm")">Save</button>
            `
        }
        let newDataType;
        switch (dataType){
            case 'H':
                newDataType = 'Depth';
            case 'Q':
                newDataType = 'Discharge';
            case 'Z':
                newDataType = 'Elevation';
            default:
                newDataType = 'Velocity';
        }

        return `
            <h1><small>Boundary ` + id + `</small></h1>
            <table class='table'>
                <tr>
                    <th scope="row">Type</th>
                    <td>`+ type + `</td>
                </tr>
                <tr>
                    <th scope="row">Data Type</th>
                    <td>`+ newDataType + `</td>
                </tr>
            </table>
        `
    }, 
    //function to configure boundary popup
    boundaryLinePopupConfig: (popup) => {
        //define popup alteration saving
        popup.on('popupopen', e => { // function to handle the saving of the data
            if(MyFunctions.deleting) { //if the user os deleting prevent popup opening
                e.target.closePopup();
                return;
            }
            setTimeout(() => { //wait in case user opens popups back to back
                if(!e.popup.isOpen()) //check if the popup is still open
                        return;
                //set the color of the current choice
                document.querySelector('#popup-current-type').style.backgroundColor = '#E8E8E8';
                document.querySelector('#popup-current-data-type').style.backgroundColor = '#E8E8E8';
                document.querySelector('#popup-btn').addEventListener('click', () => {
                    e.popup.setContent(MyFunctions.boundaryPopup(e.target._leaflet_id, document.querySelector('#popup-selected-type').value, document.querySelector('#popup-selected-data-type').value));
                    e.popup.update();
                    
                    document.querySelector('#boundaryline-' + e.target._leaflet_id + '-type-value').value = document.querySelector('#popup-selected-type').value;
                    document.querySelector('#boundaryline-' + e.target._leaflet_id + '-datatype-value').value = document.querySelector('#popup-selected-data-type').value;
                    MyFunctions.boundaryLineTreeOptionsHighlight(e.target._leaflet_id);

                    setTimeout(() => { e.target.closePopup();}, 1500);
                });
            }, 500);
        });
    },
    //function to return polygons CL popups
    polygonsPopup: (id, name, CL) => {
        if(MyFunctions.mode == 'edit') {
            return `
                <h1><small id='popup-header'>` + name + ' ' + id + `</small></h1>
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
                <div class"container">
                    <button type="button" id='popup-btn' class="btn btn-outline-info btn-sm")">Save</button>
                    <button type="button" id='popup-btn-send-to-back' class="btn btn-outline-info btn-sm")" style="float: right">Send to Back</button>
                </div>
            `
        }
        return `
            <h1><small id='popup-header'>` + name + ' ' + id + `</small></h1>
            <table class='table'>
                <tr>
                    <th scope="row">CL</th>
                    <td id='popup-current-cl'>`+ CL + `</td>
                </tr>
            </table>
        `
    },
    //function to configure polygon popup
    polygonsPopupConfig: (popup) => {
        popup.on('popupopen', e => { //define popup alteration saving
            if(MyFunctions.deleting)
                return;
            
            setTimeout(() => { //wait in case user opens popups back to back
                if(!e.popup.isOpen()) //check if the popup is still open
                    return;
                document.querySelector('#popup-btn').addEventListener('click', () => {
                    //change value in polygon tree
                    document.querySelector('#polygon-' + e.target._leaflet_id + '-CL-value').innerHTML = '<b>Current CL:</b> ' + document.querySelector('#popup-selected-cl').value;
                    e.popup.setContent(MyFunctions.polygonsPopup(e.target._leaflet_id, document.querySelector('#popup-header').innerHTML.split(' ')[0], document.querySelector('#popup-selected-cl').value));
                    e.popup.update();
                    setTimeout(() => { e.target.closePopup();}, 1500);
                });
                
                document.querySelector('#popup-btn-send-to-back').addEventListener('click', () => {
                    e.target.bringToBack()
                    MyFunctions.overlayOrder(false);
                    setTimeout(() => { e.target.closePopup();}, 500);
                });
            }, 500);
        });
    },
    //function to create domain marker popup, used to associate a sensor
    sensorAssociationPopup: (id, associatedSensors, newSensor) => {
        //('hydrometricSensor','HydrometricSensor'),  ('weatherSensor','WeatherSensor'),  ('socialNetworkScanner','SocialNetworkScanner'),  ('humanSensor','HumanSensor')
        //('physicalFixed ','PhysicalFixed '),  ('physicalMobile','PhysicalMobile'),  ('digitalSocialNetworkScanner','DigitalSocialNetworkScanner'),  ('digitalHumanUpload','DigitalHumanUpload')
        getAssociatedSensors = () => {
            if(associatedSensors === null)
                return "";

            var result;
            result = associatedSensors.slice(associatedSensors.indexOf('<tbody>') + '<tbody>'.length + 1,
                                            associatedSensors.indexOf('</tbody>'));
            return result;
        };

        associateNewSensors = () => {
            if(newSensor === null)
                return "";

            var sensor = MyFunctions.sensors.find((value) => {
                return value.code == newSensor});
                
            if(sensor === undefined) {
                return "";
            }

            var nr = '1';
            if(associatedSensors.lastIndexOf('<th>Sensor ') != -1) {
                nr = associatedSensors.slice(associatedSensors.lastIndexOf('<th>') + '<th>'.length, associatedSensors.lastIndexOf('</th>'));
                nr = Number(nr) + 1
            }

            //change popup color to associated (crimson)
            MyFunctions.contextSensors[sensor.code].options.icon.options.html = MyFunctions.sensorIcon(sensor.code, 'crimson');
            MyFunctions.contextSensors[sensor.code].refreshIconOptions();

            return `
                <tr id='sensor-` +  sensor.code + `'>
                    <th>` + nr + `</th>
                    <td class='add-code'>` + sensor.code + `</td>
                    <td>` + sensor.type + `</td>
                    <td><span class='close'>x</span></td>
                </tr>`;
        };

        if(MyFunctions.mode == 'edit') {
            return `
                <h1><small id='popup-header'>Water Entry Point ` + id + `</small></h1>
                <h2><small>Sensors</small></h2>
                <table class='table'>
                    <thead>
                        <tr>
                            <th scope="col">#</th>
                            <th scope="col">Code</th>
                            <th scope="col">Type</th>
                        </tr>
                    </thead>
                    <tbody>
                ` + getAssociatedSensors().concat(associateNewSensors()) +
                `</tbody>
                </table>
                <label for="sensor-association"><big>Choose a sensor:</big></label>
                <select id='sensor-association' class="form-control form-control-sm">
                    <option value='null'>--------------------</option>
                </select>
                <div class"container">
                    <button type="button" id='popup-btn' class="btn btn-outline-info btn-sm")">Add</button>
                </div>
            `   
        }

        return `
            <h1><small id='popup-header'>Water Entry Point ` + id + `</small></h1>
            <h2><small>Sensors</small></h2>
            <table class='table'>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Code</th>
                        <th scope="col">Type</th>
                    </tr>
                </thead>
                <tbody>
            ` + getAssociatedSensors().concat(associateNewSensors()) +
            `</tbody>
            </table>`
    },
    //functio to configure domain marker popup
    sensorAssociationPopupConfig: (popup) => {
        var sensorDistance = 100; //variable to store the distance at which a user can associate a sensor (meters)
        popup.on('popupopen', e => {
            if(MyFunctions.deleting || document.querySelector('#polygon-type').value == 'Boundary') {
                popup.closePopup();
                return;
            }
            
            setTimeout(() => { //wait in case user opens popups back to back
                if(!e.popup.isOpen()) //check if the popup is still open
                    return;
                document.querySelector('#popup-btn').addEventListener('click', () => {
                    if(document.querySelector('#sensor-association').value == 'null')
                        return;
                    e.popup.setContent(MyFunctions.sensorAssociationPopup(e.target._leaflet_id, e.popup.getContent(), document.querySelector('#sensor-association').value));
                    popup.closePopup();
                    popup.openPopup();
                });
                if(document.querySelector('.close') !== null) {
                    document.querySelectorAll('.close').forEach( element => {
                        element.addEventListener('click', ev => { //button to remove added sensors
                            MyFunctions.removeAssociatedSensor(e.popup, ev.target.parentElement.parentElement.id);
                            popup.closePopup();
                            popup.openPopup();
                        });
                    });
                }
                //fill the sensors selection options
                //check the already added sensors
                var addedSensors= [];
                document.querySelectorAll('.add-code').forEach(element => {
                    addedSensors.push(element.innerHTML);
                });
                //add the option for the available sensors for adding
                var option;
                for(sensor of MyFunctions.sensors) {
                    if(!addedSensors.includes(sensor.code) && //verify if the sensor is already added and is close enough
                        L.latLng(e.target.getLatLng()).distanceTo(L.latLng(MyFunctions.coordStringToArray(sensor.geom)[0])) <= sensorDistance) { 
                        option = document.createElement('option');
                        option.value = sensor.code;
                        option.innerHTML = sensor.code.concat(' '.concat(sensor.type));
                        document.querySelector('#sensor-association').appendChild(option);
                    }
                };
            }, 500);
        });
    },
    //function to remove row from associated sensors
    removeAssociatedSensor: (popup, sensorCode) => {
        let begginning = popup.getContent().substring(0, popup.getContent().indexOf('<tr id=\''.concat(sensorCode)));
        let ending = popup.getContent().substr(popup.getContent().indexOf('</tr>', popup.getContent().indexOf('<tr id=\''.concat(sensorCode))) + '</tr>'.length);
        popup.setContent(begginning.concat(ending));

        //change popup color to not associated (whitesmoke)
        let code = sensorCode.split('-')[1];
        MyFunctions.contextSensors[code].options.icon.options.html = MyFunctions.sensorIcon(code, 'whitesmoke');
        MyFunctions.contextSensors[code].refreshIconOptions();
    },
    //function to run everytime a overlay is added to keep the polygons ordered (alignment is boolean and defines if alignment layer is to be brought to front)
    overlayOrder: (alignment) => {
        MyFunctions.createdPolygons.Domain.invoke('bringToBack');
        MyFunctions.createdPolygons.Boundaries.invoke('bringToFront');
        if(alignment) //check if alignment is supposed to be brought to front
            MyFunctions.createdPolygons.Alignment.invoke('bringToFront');
    },
    //function to set the domain markers layers visibility toggle
    setDomainMarkers: (map) => {
        MyFunctions.domainMarkers = L.markerClusterGroup({showCoverageOnHover: false});
        MyFunctions.domainMarkers.addTo(map);
        map.layerscontrol.addOverlay(MyFunctions.domainMarkers, "Domain markers");

        MyFunctions.domainMarkers.on('popupopen', e => {
            if(document.querySelector("#polygon-type").value === 'Boundary') {
                e.target.closePopup();
                MyFunctions.highlightStatus = false; //keep the highlight functionality disabled
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

            if(MyFunctions.mode == 'edit' && document.querySelector("#polygon-type").value === 'Boundary' && MyFunctions.boundaryPolyline != null) { //if the user is drawing the boundary
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
            MyFunctions.addDomainMarker(map, [lat, lng]);
            //console.log(domain.getBounds());
        }
    },
    //function to redraw the domain markers when the edit stops
    editStop: (map) => {
        let coordinates = MyFunctions.createdPolygons.Domain.getLayers()[0].getLatLngs()[0];
        for(coordinate of coordinates) {//populate the vertices with markers again
            MyFunctions.addDomainMarker(map, coordinate);
        }
    },
    //function to delete layers from created polygons when deleting from editPolygonFeature
    removeLayers: (layers) => {
        for(layer of layers) {
            if(MyFunctions.createdPolygons.Domain.hasLayer(layer)) {
                MyFunctions.createdPolygons.Boundaries.clearLayers();
                MyFunctions.domainMarkers.clearLayers();
                MyFunctions.domainMarkerToBoundary = {};

                while(document.querySelector('#boundaryline-tree-id').firstChild)
                    document.querySelector('#boundaryline-tree-id').lastChild.remove();

                MyFunctions.createdPolygons.Domain.removeLayer(layer);

                document.querySelector('#polygon-tree-Domain-' + layer._leaflet_id).remove();
            }

            else if(MyFunctions.createdPolygons.Refinement.hasLayer(layer)) {
                MyFunctions.createdPolygons.Refinement.removeLayer(layer);
                document.querySelector('#polygon-tree-Refinement-' + layer._leaflet_id).remove();
            }

            else if(MyFunctions.createdPolygons.Alignment.hasLayer(layer)) {
                MyFunctions.createdPolygons.Alignment.removeLayer(layer);
                document.querySelector('#polygon-tree-Alignment-' + layer._leaflet_id).remove();
            }
        }

        //remove polygon tree
        MyFunctions.deleting = false;
    },
    //function to remove domain markers
    clearLayers: () => {
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.createdPolygons.Boundaries.clearLayers();
        MyFunctions.domainMarkerToBoundary = {};
    },
    //function to add domain marker
    addDomainMarker: (map, latLng, sensors) => {
        let marker = L.marker(latLng).addTo(MyFunctions.domainMarkers);

        MyFunctions.sensorAssociationPopupConfig(marker.bindPopup(MyFunctions.sensorAssociationPopup(marker._leaflet_id, null, null)));

        if(sensors !== undefined) {
            for(sensor of sensors) {
                marker.getPopup().setContent(MyFunctions.sensorAssociationPopup(marker._leaflet_id, marker.getPopup().getContent(), sensor.sensor));
            }
        }
        
        //add the logic to draw the boundary based on the domain polygon vertex
        marker.on('click', e => {
            if(document.querySelector("#polygon-type").value === 'Boundary') {
                if(MyFunctions.boundaryPolyline === null) { //if it's the first point of the polyline being added to the map then
                    MyFunctions.boundaryPolyline = L.polyline([latLng], color='#0000A0').addTo(map);
                    //start saving the markers
                    MyFunctions.boundaryPolylineMarkersTemp = []; 
                    MyFunctions.boundaryPolylineMarkersTemp.push(marker);
                }
                else { //if there are already defined points then draw the polyline
                    //add some logic to guarantee that the points are sequential in the array
                    MyFunctions.boundaryPolyline.addLatLng(latLng);
                    MyFunctions.tempPolyline.setLatLngs([latLng, MyFunctions.tempPolyline.getLatLngs()[1]]);
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
            MyFunctions.highlightStatus = true; //enable highlights again
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
            var boundaryPoints = {"type": "FeatureCollection", "features": []};
            MyFunctions.createdPolygons.Boundaries.getLayers().forEach((element) => {
                boundaryLine = element.toGeoJSON();
                popup = element.getPopup().getContent(); //get the popup to extract the properties values
                boundaryLine.properties.id = element._leaflet_id;
                boundaryLine.properties.type = popup.slice(popup.indexOf('current-type\' value="') + 'current-type\' value="'.length, popup.indexOf('" selected')).trim();
                boundaryLine.properties.dataType = popup.substr(popup.indexOf('data-type\' value="') + 'data-type\' value="'.length, 1).trim();
                for(point of MyFunctions.domainMarkerToBoundary[element._leaflet_id]) { //get sensors associated with points
                    boundaryPoint = point.toGeoJSON();
                    pointPopup = point.getPopup().getContent();                
                    
                    boundaryPoint.properties.boundaryLineId = element._leaflet_id; //associate with boundary line
                    
                    let sensors = [];
                    if((codes = pointPopup.match(/<td class=("|')add-code("|')>(.)*<\/td>/g)) != null) {
                        for(code of codes) 
                            sensors.push(code.slice('<td class="add-code">'.length, code.indexOf('</td>')));
                    }
                    boundaryPoint.properties.sensors = sensors;

                    boundaryPoints.features.push(boundaryPoint);
                }
                boundaries.features.push(boundaryLine);
            });
            document.querySelector('#id_boundaries').value = JSON.stringify(boundaries);
            document.querySelector('#id_boundary_points').value = JSON.stringify(boundaryPoints);
            
            // Check if the drawing is fully completed
            if(MyFunctions.complete) {
                document.querySelector('#load-context-result').innerHTML = "Context staged!";
                document.querySelector('#load-context-result').className = "alert alert-success";
            }
            else {
                let missing = 'Context staged but incomplete<br>';
                let text = document.querySelector('#load-context-result').innerHTML.split('<br>');
                for(i = 1; i < text.length - 1; i++) {
                    missing += text[i] + '<br>';
                }
                missing += text[text.length - 1];
                document.querySelector('#load-context-result').innerHTML = missing;
            }
            document.querySelector('#submit-btn').disabled = false;
            document.querySelector('#submit-btn').setAttribute("class", "btn btn-outline-info");
            document.querySelector('#submit-btn').innerHTML = 'Save Context'
        }
        catch(err) { //In case of invalid context
            console.log(err);
            document.querySelector('#load-context-result').setAttribute("class", "alert alert-danger");
            document.querySelector('#load-context-result').innerHTML = "Unable to save Context<br>Hint: Start by drawing the Domain";
        }
        finally {
            // document.querySelector('#load-context-result').style.display = 'block';
            MyFunctions.pruneDomainMarkers();
        }
    },
    //function to delete all domain points that dont belong to a boundary line
    pruneDomainMarkers: () => {
        MyFunctions.domainMarkers.eachLayer((marker) => {
            let found = false;
            for(line in MyFunctions.domainMarkerToBoundary) {
                if(found)
                    break;
                for(point of MyFunctions.domainMarkerToBoundary[line]) {
                    if(point._leaflet_id === marker._leaflet_id) {
                        found = true;
                        break;
                    }
                }
            }
            if(!found)
                MyFunctions.domainMarkers.removeLayer(marker);
        })
    },
    //function to get a context to edit
    getContext: (url, map) => {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", url, false); 
        xmlHttp.send(null);
        response = JSON.parse(xmlHttp.responseText);

        //show the form
        if(MyFunctions.mode == 'edit') {
            document.querySelector('#form-data').style.display = 'block';
            document.querySelector('#polygon-tree-id').style.height = '' + document.querySelector('#map-container').offsetHeight + 'px';
            MyFunctions.fillForm(response);
        }
        
        console.log(response);

        MyFunctions.drawGeometries(response, map);

        map.setView(MyFunctions.createdPolygons.Domain.getLayers()[0].getCenter(), 12);

        //get DTM if it exists
        if(response.context_dtm !== null) 
            L.tileLayer(`http://127.0.0.1:8000/context/raster/tiles/${response.context_dtm.contextDTM}/{z}/{x}/{y}.png`).addTo(MyFunctions.dtm);
    },
    //function to clear the map to fill with new data
    clearMap: () => {
        MyFunctions.createdPolygons.Boundaries.clearLayers();
        MyFunctions.domainMarkerToBoundary = {};
        MyFunctions.domainMarkers.clearLayers();
        MyFunctions.editPolygonFeature.clearLayers();
        MyFunctions.dtm.clearLayers();

        for(key in MyFunctions.createdPolygons)
            MyFunctions.createdPolygons[key].clearLayers();

        var element = document.querySelector('#domain-tree-id');
        while(element.firstChild)
            element.lastChild.remove();
        
        element = document.querySelector('#refinement-tree-id');
        while(element.firstChild)
            element.lastChild.remove();
        
        element = document.querySelector('#alignment-tree-id');
        while(element.firstChild)
            element.lastChild.remove();
        
        element = document.querySelector('#boundaryline-tree-id');
        while(element.firstChild)
            element.lastChild.remove();

        // Change sensor colors to white
        for(code in MyFunctions.contextSensors) {
            MyFunctions.contextSensors[code].options.icon.options.html = MyFunctions.sensorIcon(code, 'whitesmoke');
            MyFunctions.contextSensors[code].refreshIconOptions();
        }
    },
    //function to fill the form when the context with the api is called
    fillForm: (response) => {
        document.querySelector('#id_code').value = response.code;
        document.querySelector('#id_name').value = response.Name;
        document.querySelector('#id_hydroFeature').value = response.hydroFeature;
    },
    //function to draw the geometries in the context from API call
    drawGeometries: (response, map) => {
        //Domain
        if(response.geomExternalBoundary !== null) { //check if the refinement is defined in the database
            let domain = L.polygon(MyFunctions.coordStringToArray(response.geomExternalBoundary), {color: '#C0C0C0'});
            MyFunctions.definePolygon(domain, "Domain", response.CLExternalBoundary);
            // MyFunctions.editStop(map); //draw the markers
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
                //Boundary Points
                for(point of element.context_boundary_points) {
                    MyFunctions.addDomainMarker(map, MyFunctions.coordStringToArray(point.geom)[0], point.sensor_boundary_point);
                }
                //Boundary Lines
                boundary = L.polyline(MyFunctions.coordStringToArray(element.geom));
                MyFunctions.defineBoundary(boundary, element.type, element.dataType);
            });
        }
        // if(MyFunctions.mode == 'edit' && response.context_contour_lines !== null) {
        //     let coordinates = [];
        //     lines = response.context_contour_lines.geom.slice(response.context_contour_lines.geom.indexOf('(') + 1, response.context_contour_lines.geom.lastIndexOf(')'))
        //     lines = lines.split('),')
        //     for(line of lines) {
        //         line = line.slice(1).split(',');
        //         for(coord of line) {
        //             coordinates.push([Number(coord.trim().split(' ')[1]), Number(coord.trim().split(' ')[0])]);
        //         }
        //         L.polyline(coordinates).addTo(map)
        //         coordinates = []
        //     }
        // }
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

        if(MyFunctions.mode == 'edit')
            MyFunctions.polygonsPopupConfig(layer.bindPopup(MyFunctions.polygonsPopup(L.stamp(layer), type, CL)));
        else
            layer.bindPopup(MyFunctions.polygonsPopup(L.stamp(layer), type, CL))
        
        layer.bindTooltip(type + ' ' + layer._leaflet_id);
        polygonLayer.addLayer(layer); //Domain

        MyFunctions.handleHighlights(layer, polygonLayer);
        
        if(MyFunctions.mode == 'edit') {
            MyFunctions.checkForCompleteness();
            MyFunctions.editPolygonFeature.addLayer(layer); //Add to this layer for editing
            MyFunctions.addPolygonToTree(layer._leaflet_id, type, CL);
        }
    },
    //function to define boundary and draw it on the map
    defineBoundary: (boundary, type, dataType) => {
        boundary.setStyle({color: '#008080'});
        MyFunctions.createdPolygons.Boundaries.addLayer(boundary);
        if(MyFunctions.mode == 'edit')
            MyFunctions.boundaryLinePopupConfig(boundary.bindPopup(MyFunctions.boundaryPopup(boundary._leaflet_id, type, dataType)));
        else
            boundary.bindPopup(MyFunctions.boundaryPopup(boundary._leaflet_id, type, dataType))
        boundary.bindTooltip("Boundary " + boundary._leaflet_id);
        MyFunctions.handleHighlights(boundary, MyFunctions.createdPolygons.Boundaries);

        //associate point to respective boundary
        var boundaryPoints = [];
        for(boundaryLinePoint of boundary.getLatLngs()) {
            for(domainPoint of MyFunctions.domainMarkers.getLayers()) {  
                if(boundaryLinePoint.distanceTo(domainPoint.getLatLng()) < 1) { //this distance is very sensitive and can cause the duplication of points
                    boundaryPoints.push(domainPoint);
                    domainPoint.bindTooltip('Boundary Point ' + domainPoint._leaflet_id);
                }
            }
        }
        MyFunctions.domainMarkerToBoundary[boundary._leaflet_id] = boundaryPoints;
        
        if(MyFunctions.mode == 'edit') {
            MyFunctions.checkForCompleteness();
            boundary.on('dblclick', e => {
                e.target.removeFrom(MyFunctions.createdPolygons.Boundaries);
                document.querySelector('#boundaryline-tree-id-' + e.target._leaflet_id).remove();
            });
            MyFunctions.addBoundaryLineToTree(boundary._leaflet_id, type, dataType);

            // for(point of boundaryPoints) {
            //     MyFunctions.addBoundaryPointToTree(point._leaflet_id, [], boundary._leaflet_id);
            // }
        }
    },
    //check if all layers of createdPolygons have polygons 
    checkForCompleteness: () => {
        let missingPolygons = '';
        MyFunctions.complete = true;
        for(type in MyFunctions.createdPolygons) { //check if all polygons are defined
            if(MyFunctions.createdPolygons[type].getLayers().length < 1) {
                missingPolygons += type +' missing<br>'
                document.querySelector('#load-btn').setAttribute('class', "btn btn-outline-warning");
                // document.querySelector('#load-btn').disabled = true;
                MyFunctions.complete = false;
            }
        }
        if(MyFunctions.complete) {
            document.querySelector('#load-btn').setAttribute('class', "btn btn-outline-info"); //all polygons are defined mark the button green
            document.querySelector('#load-context-result').innerHTML = "Context complete stage it!";
            document.querySelector('#load-context-result').className = "alert alert-success";
        }
        else {
            document.querySelector('#load-context-result').setAttribute("class", "alert alert-warning");
            document.querySelector('#load-context-result').innerHTML = "Context incomplete but ready for submission<br>" + missingPolygons;
        }
        // document.querySelector('#load-btn').disabled = false;
    },
    //function to handle highlights
    handleHighlights: (layer, polygonLayer) => {
        MyFunctions.highlightStatus = true;
        let polygonType = false; //polygon
        if(polygonLayer === MyFunctions.createdPolygons.Boundaries || polygonLayer === MyFunctions.createdPolygons.Alignment)
            polygonType = true; //polyline
        
        layer.on('mouseover', e => { if(MyFunctions.highlightStatus) { MyFunctions.highlightPolygon(e.target._leaflet_id, polygonType, polygonLayer);}});
        layer.on('mouseout', () => {
            if(MyFunctions.highlightStatus)
                MyFunctions.highlightLayer.clearLayers();
        });
        layer.on('click', e => {
            MyFunctions.highlightLayer.clearLayers();
            MyFunctions.highlightPolygon(e.target._leaflet_id, polygonType, polygonLayer);
        });
    },
    //function to highlight a polygon
    highlightPolygon: (polygonId, polygonType, polygonLayer) => {
        if(polygonType)
            L.polyline(polygonLayer.getLayer(polygonId).getLatLngs(), {interactive: false}).addTo(MyFunctions.highlightLayer);
        else
            L.polygon(polygonLayer.getLayer(polygonId).getLatLngs(), {interactive: false}).addTo(MyFunctions.highlightLayer);
    },
    //function to transform coordinate string into an array
    coordStringToArray: (string) => {
        let coordinates = [];
        string = string.slice(string.lastIndexOf('(') + 1, string.indexOf(')')).split(',');
        for(coord of string)
            coordinates.push([Number(coord.trim().split(' ')[1]), Number(coord.trim().split(' ')[0])]);
        return coordinates;
    },
    //functions for polygon tree
    //adds a polygon to the tree
    addPolygonToTree: (id, polygon, CL) => {
        let polygonType, polygonLayer;
        const element = new DOMParser().parseFromString(MyFunctions.polygonInTreeHTML(id, polygon, CL), 'text/html').firstChild.lastChild.firstChild;
        switch(polygon) {
            case 'Domain':
                document.querySelector('#domain-tree-id').appendChild(element);
                polygonType = false;
                polygonLayer = MyFunctions.createdPolygons.Domain;
                break;
            case 'Refinement':
                document.querySelector('#refinement-tree-id').appendChild(element);
                polygonType = false;
                polygonLayer = MyFunctions.createdPolygons.Refinement;
                break;
            case 'Alignment':
                document.querySelector('#alignment-tree-id').appendChild(element);
                polygonType = true;
                polygonLayer = MyFunctions.createdPolygons.Alignment;
        }

        element.addEventListener('mouseover', () => { if(MyFunctions.highlightStatus) { MyFunctions.highlightPolygon(id, polygonType, polygonLayer);}});
        element.addEventListener('mouseout', () => {
            if(MyFunctions.highlightStatus)
                MyFunctions.highlightLayer.clearLayers();
        });


        document.querySelector('#polygon-' + id + '-CL-input-btn').addEventListener('click', () => {
            polygonLayer.getLayer(id).getPopup().setContent(MyFunctions.polygonsPopup(id , polygon, document.querySelector('#polygon-' + id + '-CL-input').value));
            document.querySelector('#polygon-' + id + '-CL-value').innerHTML = '<b>Current CL:</b> ' + document.querySelector('#polygon-' + id + '-CL-input').value;
            document.querySelector('#polygon-' + id + '-CL-input').value = '';
        });
    },
    //adds a boundary line to the tree
    addBoundaryLineToTree: (id, selectedType, selectedDataType) => {
        const element = new DOMParser().parseFromString(MyFunctions.boundaryLineInTreeHTML(id, selectedType, selectedDataType), 'text/html').firstChild.lastChild.firstChild;
        document.querySelector('#boundaryline-tree-id').appendChild(element);

        element.addEventListener('mouseover', () => { if(MyFunctions.highlightStatus) { MyFunctions.highlightPolygon(id, true, MyFunctions.createdPolygons.Boundaries);}});
        element.addEventListener('mouseout', () => {
            if(MyFunctions.highlightStatus)
                MyFunctions.highlightLayer.clearLayers();
        });

        document.querySelector('#boundaryline-' + id + '-type-value').options[document.querySelector('#boundaryline-' + id + '-type-value').selectedIndex].style.backgroundColor = '#E8E8E8';
        document.querySelector('#boundaryline-' + id + '-datatype-value').options[document.querySelector('#boundaryline-' + id + '-datatype-value').selectedIndex].style.backgroundColor = '#E8E8E8';
        
        document.querySelector('#boundaryline-' + id + '-types-input-btn').addEventListener('click', () => {
            MyFunctions.createdPolygons.Boundaries.getLayer(id).getPopup()
            .setContent(MyFunctions.boundaryPopup(id, document.querySelector('#boundaryline-' + id + '-type-value').value, document.querySelector('#boundaryline-' + id + '-datatype-value').value));

            MyFunctions.boundaryLineTreeOptionsHighlight(id);
        });
    },
    //adds a boundary point to the tree
    addBoundaryPointToTree: (id, addedSensors, boundaryLine) => {
        const element = new DOMParser().parseFromString(MyFunctions.boundaryPointInTreeHTML(id, addedSensors), 'text/html').firstChild.lastChild.firstChild;
        document.querySelector('#boundaryline-tree-id-' + boundaryLine).appendChild(element);
    },
    //write polygon html for tree
    polygonInTreeHTML: (id, polygonType, CL) => {
        return `
            <div ` + 'id=polygon-tree-' + polygonType + '-' + id + ` class="polygon-tree container border-bottom">
                <div class="row">
                    <div class="col-md-12" polygon-tree-label">
                        <span class="tree-titles"><b>` + polygonType + ' ' + id + `</b></span>
                    </div>
                </div>
                <div ` + 'id=polygon-' + id + '-CL-value' + ` class="row">
                    <div class="col-md-12">
                        <b>Current CL:</b> ` + CL + `
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="input-group mb-3">
                            <input type="text" ` + 'id=polygon-' + id + '-CL-input' + ` class="form-control" placeholder="Insert new CL">
                            <div class="input-group-append">
                                <button type="button" ` + 'id=polygon-' + id + '-CL-input-btn' + ` class="btn btn-outline-info">Save</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    //write boundary line html for tree
    boundaryLineInTreeHTML: (id, selectedType, selectedDataType) => {
        findSelected = (valueInAnalisys, selected) => {
            if(valueInAnalisys == selected)
                return 'selected';
            else
                return '';
        }

        return `
            <div ` + 'id=boundaryline-tree-id-' + id + ` class="polygon-tree container border-bottom">
                <div class="row">
                    <div class="col-md-12" style="margin-bottom:5px;">
                        <span class="tree-titles"><b>Boundary ` + id + `</b></span>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 polygon-tree-label">
                        <b>Type:</b>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="input-group mb-3">
                            <select ` + 'id=boundaryline-' + id + '-type-value' + ` class="custom-select">
                                <option value="Input" ` + findSelected('Input', selectedType) + `>Input</option>
                                <option value="Output" ` + findSelected('Output', selectedType) + `>Output</option>
                                <option value="InputOutput" ` + findSelected('InputOutput', selectedType) + `>Input Output</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 polygon-tree-label" style="margin-top:-8px">
                        <b>Data Type:</b>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="input-group mb-3">
                            <select ` + 'id=boundaryline-' + id + '-datatype-value' + ` class="custom-select">
                                <option value="H" ` + findSelected('H', selectedDataType) + `>Depth</option>
                                <option value="Q" ` + findSelected('Q', selectedDataType) + `>Discharge</option>
                                <option value="Z" ` + findSelected('Z', selectedDataType) + `>Elevation</option>
                                <option value="V" ` + findSelected('V', selectedDataType) + `>Velocity</option>
                            </select>
                            <div class="input-group-append">
                                <button type="button" ` + 'id=boundaryline-' + id + '-types-input-btn' + ` class="btn btn-outline-info">Save</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    //write boundary point html for tree
    boundaryPointInTreeHTML: (id, addedSensors) => {
        buildAssociatedSensorsTableBody = () => {
            return `
                <tr>
                    <th>1</th>
                    <td class='add-code'>5</td>
                    <td>Input</td>
                    <td><span class='close'>x</span></td>
                </tr>
            `
        }

        buildOptions = () => {
            let addOptions = '';
            let availableSensors = MyFunctions.getNearbySensors(addedSensors, MyFunctions.domainMarkers.getLayer(id));

            for(option of availableSensors) {
                addOptions += option.outerHTML;
            }

            console.log('Sensors ' + id)
            console.log(MyFunctions.getNearbySensors(addedSensors, MyFunctions.domainMarkers.getLayer(id)))
            console.log(addOptions)
            return addOptions;

            // option = document.createElement('option');
            // option.value = sensor.code;
            // option.innerHTML = sensor.code.concat(' '.concat(sensor.type));
            // document.querySelector('#sensor-association').appendChild(option);
        }

        return `
            <div ` + 'id=boundarypoint-tree-id-' + id + ` class="polygon-tree col-md-12 border-top border-bottom">
                <div class="col-md-4">
                    <h1><small>Water Entry Point ` + id + ` Sensors</small></h1>
                </div>
                <div class="col-md-8">
                    <table class='table'>
                        <thead>
                            <tr>
                                <th scope="col">#</th>
                                <th scope="col">Code</th>
                                <th scope="col">Type</th>
                            </tr>
                        </thead>
                        <tbody>`
                            + buildAssociatedSensorsTableBody() +
                        `</tbody>
                    </table>
                    <div class="input-group col-md-12">
                        <div class="input-group-prepend">
                            <span class="input-group-text"><b>Choose a sensor:</b></span>
                        </div>
                        <select name="sensor-association-tree" class="custom-select">
                            <option value='null'>--------------------</option>
                            ` + buildOptions() + `
                        </select>
                        <div class"input-group-append">
                            <button type="button" class="btn btn-outline-info">Add</button>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    //function to highlight the background color of current value of boundary line options in polygonTree
    boundaryLineTreeOptionsHighlight: (id) => {
        for(node of document.querySelector('#boundaryline-' + id + '-type-value').childNodes) {
            if(node.style !== undefined)
                node.style.backgroundColor = 'white';
        }
        for(node of document.querySelector('#boundaryline-' + id + '-datatype-value').childNodes){
            if(node.style !== undefined)
                node.style.backgroundColor = 'white';
        }

        document.querySelector('#boundaryline-' + id + '-type-value').options[document.querySelector('#boundaryline-' + id + '-type-value').selectedIndex].style.backgroundColor = '#E8E8E8';
        document.querySelector('#boundaryline-' + id + '-datatype-value').options[document.querySelector('#boundaryline-' + id + '-datatype-value').selectedIndex].style.backgroundColor = '#E8E8E8';
    },
    //function to get sensors that are close enough to a marker
    getNearbySensors: (addedSensors, domainPoint) => {
        let nearbySensors = [], sensorDistance = 100
        for(sensor of MyFunctions.sensors) {
            if(!addedSensors.includes(sensor.code) && //verify if the sensor is already added and is close enough
                L.latLng(domainPoint.getLatLng()).distanceTo(L.latLng(MyFunctions.coordStringToArray(sensor.geom)[0])) <= sensorDistance) { 
                option = document.createElement('option');
                option.value = sensor.code;
                option.innerHTML = sensor.code.concat(' '.concat(sensor.type));
                nearbySensors.push(option);
            }
        };
        return nearbySensors;
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