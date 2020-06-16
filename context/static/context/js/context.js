document.addEventListener('DOMContentLoaded', () => {
    window.addEventListener("map:init", e => {
        const map = e.detail.map;
        alert('oi');
        //create a div on the map to see the current mouse lat and lon
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

        
    });
});