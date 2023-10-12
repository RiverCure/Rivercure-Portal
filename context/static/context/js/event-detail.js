async function requestEvent() {
    var intervalId = setInterval(() => {
        const xhr = new XMLHttpRequest();
        const url = statusUrl;
        xhr.open('GET', url, true);
        xhr.responseType="json";
        xhr.onload =  (e) => {
            const request = e.target;
            const result = request.response;
            if(request.status == 200 && result.status == "Finished successfully") {
                clearInterval(intervalId);
                location.reload(true);
            }
        };

        xhr.send(null);
    }, 5000);
}

function loadMap() {
    // initalize leaflet map
    const map = L.map("map", {
        fullscreenControl: true,
    }).setView([0, 0], 5);

    // add OpenStreetMap basemap
    L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png", {
        attribution:
            '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    return map;
}

async function loadUrls(rasters) {
    const georasters = {};
    // Could also do this in parallel: https://stackoverflow.com/questions/37576685/using-async-await-with-a-foreach-loop
    let min, max, range = 0;
    for (const key of Object.keys(rasters)) {
        const url = rasters[key];
        if(!url) continue;

        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        const georaster = await parseGeoraster(arrayBuffer);
        min = georaster.mins[0];
        max = georaster.maxs[0];
        range = georaster.ranges[0];
        georasters[key] = georaster;
    }
    return { georasters, min, max, range };
}

function placeInMap(map, georasters, min, max, range) {
    /*
        GeoRasterLayer is an extension of GridLayer,
        which means can use GridLayer options like opacity.

        Just make sure to include the georaster option!

        http://leafletjs.com/reference-1.2.0.html#gridlayer
    */
   if(!Object.keys(georasters).length) return;

   const layers = {};
   for(const key of Object.keys(georasters)) {
        let layer = new GeoRasterLayer({
            georaster: georasters[key],
            // georasters: georasters,
            opacity: 0.7,
            resolution: 256,
            pixelValuesToColorFn: (pixelValues) => {
                const pixelValue = pixelValues[0]; // there's just one band in this raster
                const scale = chroma.scale("Viridis");

                // if there's zero wind, don't return a color
                if (pixelValue === 0) return null;

                const scaledPixelValue = (pixelValue - min) / range;
                const color = scale(scaledPixelValue).hex();

                return color;
            },
        });
        layers[key] = layer;
   }

   const firstLayer = layers[Object.keys(layers)[0]];
   // Add first layer as it will be the pre-selected one
   firstLayer.addTo(map);
    
    L.control.layers(null, layers).addTo(map);
    // Toggle to this if they want to only have 1 selected at a time
    // L.control.layers(layers).addTo(map);

    // Center to the first layer (any would do)
    map.fitBounds(firstLayer.getBounds());

    // Show map
    // document.getElementById('map-container').style.display = 'block';
}

async function main() {
    // console.log(rasters);
    // hasSimulation and rasters variables are declared on context/event/detail.html
    if(hasSimulation == "False") {
        // Check if mesh exists
        requestEvent();
    } else {
        const map = loadMap();
        // List of urls, removing the "null" ones
        const { georasters, min, max, range } = await loadUrls(rasters);
        placeInMap(map, georasters, min, max, range);
    }
}

main();