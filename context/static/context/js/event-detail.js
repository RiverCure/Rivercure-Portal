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
                // Give time for files to be copied
                location.reload(true);
            }
        };

        xhr.send(null);
    }, 5000);
}

function generateHumanReadableLayerNames(key) {
    switch (key) {
        case 'maxDepth':
            return 'Maximum depth';
        case 'maxLevel':
            return 'Maximum level';
        case 'maxQ':
            return 'Hazard index';
        case 'maxVel':
            return 'Maximum velocity';
        default:
            throw new Error('Key not found');
    }
}

function generateMachineReadableNames(humanReadable) {
    switch (humanReadable) {
        case 'Maximum depth':
            return 'maxDepth';
        case 'Maximum level':
            return'maxLevel';
        case 'Hazard index':
            return'maxQ';
        case 'Maximum velocity':
            return 'maxVel';
        default:
            throw new Error('Key not found');
    }
}

function generateLegendLabel(layerName) {
    switch (layerName) {
        case 'maxDepth':
            return `${generateHumanReadableLayerNames(layerName)} (m)`;
        case 'maxLevel':
            return `${generateHumanReadableLayerNames(layerName)} (m)`;
        case 'maxQ':
            return `${generateHumanReadableLayerNames(layerName)}`;
        case 'maxVel':
            return `${generateHumanReadableLayerNames(layerName)} (m/s)`;
        default:
            throw new Error('Key not found');
    }
}

// https://github.com/gka/chroma.js/blob/main/src/colors/colorbrewer.js
function getScale(layerName) {
    switch (layerName) {
        case 'maxDepth':
            // Reversed Virdis (https://github.com/gka/chroma.js/blob/main/src/colors/colorbrewer.js)
            return ['#fee825', '#b6de2b', '#6cce5a', '#1f9d8a', '#26838f', '#31678e', '#3f4a8a', '#482777', '#440154'];
        case 'maxLevel':
            return "Spectral";
        case 'maxQ':
            return ["yellow", "orange", "red"];
        case 'maxVel':
            return 'PuOr';
        default:
            throw new Error('Key not found');
    }
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
        georasters[key] = { raster: georaster, min, max, range };
    }
    return georasters;
}

function placeInMap(map, georasters) {
    /*
        GeoRasterLayer is an extension of GridLayer,
        which means can use GridLayer options like opacity.

        Just make sure to include the georaster option!

        http://leafletjs.com/reference-1.2.0.html#gridlayer
    */
   if(!Object.keys(georasters).length) return;

   const layers = {};
   for(const key of Object.keys(georasters)) {
        const georaster = georasters[key];
        let layer = new GeoRasterLayer({
            georaster: georaster.raster,
            // georasters: georasters,
            opacity: 0.7,
            resolution: 256,
            pixelValuesToColorFn: (pixelValues) => {
                const pixelValue = pixelValues[0]; // there's just one band in this raster
                if (pixelValue === 0) return null;

                let scale;
                let scaledPixelValue;
                if(key == 'maxQ') {
                    scale = chroma.scale(getScale(key)).domain([0, 2.0]);
                    scaledPixelValue = pixelValue / 2.0;
                } else {
                    scale = chroma.scale(getScale(key));
                    scaledPixelValue = (pixelValue - georaster.min) / georaster.range;
                }
                const color = scale(scaledPixelValue).hex();

                return color;
            },
        });
        layers[generateHumanReadableLayerNames(key)] = layer;
   }

   const firstLayer = layers[Object.keys(layers)[0]];
   // Add first layer as it will be the pre-selected one
   firstLayer.addTo(map);

   layers['No layer'] = L.tileLayer('');
    
    L.control.layers(layers).addTo(map);

    // Toggle to this if they want to have multiple at the same time
    // L.control.layers(null, layers).addTo(map);

    // Center to the first layer (any would do)
    map.fitBounds(firstLayer.getBounds());

    // Show map
    // document.getElementById('map-container').style.display = 'block';
}

function placeLegend(map, georasters) {
    let legend;
    
    legend = L.control({position: 'bottomright'});
    legend.onAdd = () => createLegend('maxDepth', georasters['maxDepth']); // Pre-selected layer
    legend.addTo(map);

    map.on('baselayerchange', (newLayer) => {
        // Remove old legend
        map.removeControl(legend);

        if(newLayer.name == 'No layer') return;

        const layerName = generateMachineReadableNames(newLayer.name);
        const currentLayer = georasters[layerName];

        legend = L.control({position: 'bottomright'});
        legend.onAdd = () => createLegend(layerName, currentLayer);
        legend.addTo(map);
    });
}

function createLegend(layerName, georaster) {
    const div = L.DomUtil.create('div', 'info legend');

    if(layerName == 'maxQ') {
        div.innerHTML = `
            <color-legend
                titletext="${generateLegendLabel(layerName)}"
                scaletype="continuous"
                range='["yellow", "orange", "red"]'
                tickFormat=".1f"
                domain="[0, 2.0]">
            </color-legend>`;
    } else {
        // Build scale string
        const scale = chroma.scale(getScale(layerName)).colors(8);
        let range = '\'[';
        scale.forEach((color, index, arr) => {
            if(index != arr.length - 1) {
                range += `"${color}",`;
            } else {
                range += `"${color}"]'`;
            }
        });

        // div.innerHTML = labels.join('<br>');
        div.innerHTML = `
            <color-legend
                titletext="${generateLegendLabel(layerName)}"
                scaletype="continuous"
                range=${range}
                tickFormat=".0f"
                ticks=5
                domain="[${Math.round(georaster.min)}, ${Math.round(georaster.max)}]">
            </color-legend>`;
    }

    return div;
}

async function main() {
    // hasSimulation and rasters variables are declared on context/event/detail.html
    if(hasSimulation == "False") {
        // Check if mesh exists
        requestEvent();
    } else {
        const map = loadMap();
        // List of urls, removing the "null" ones
        const georasters = await loadUrls(rasters);
        placeInMap(map, georasters);
        placeLegend(map, georasters);
    }
}

main();