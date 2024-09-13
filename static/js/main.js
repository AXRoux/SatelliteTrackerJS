let map;
let satellites = {};
let markers = {};
let pathLines = {};
let trajectoryLines = {};
let satelliteLimit = 5;

function initMap() {
    console.log('Initializing map');
    map = L.map('map').setView([config.observerLat, config.observerLon], 3);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    console.log('Map initialized');
}

function createSatelliteIcon(satellite) {
    console.log('Creating satellite icon for:', satellite.satname);
    return L.divIcon({
        className: 'satellite-icon',
        html: `<div class="satellite-dot"></div><div class="satellite-label">${satellite.satname}</div>`,
        iconSize: [100, 20],
        iconAnchor: [50, 10]
    });
}

function updateSatellitePositions() {
    console.log('Updating satellite positions');
    Object.keys(satellites).slice(0, satelliteLimit).forEach(satid => {
        fetch(`/api/satellite/${satid}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received position data for satellite:', satid, data);
                if (!data.positions || data.positions.length === 0) {
                    console.error('No position data received for satellite:', satid);
                    return;
                }
                const position = data.positions[0];
                const latlng = [position.satlatitude, position.satlongitude];
                
                if (markers[satid]) {
                    console.log('Updating existing marker for satellite:', satid);
                    markers[satid].setLatLng(latlng);
                    markers[satid].getPopup().setContent(createPopupContent(satellites[satid], position));
                    updatePathLine(satid, latlng);
                } else {
                    console.log('Creating new marker for satellite:', satid);
                    const marker = L.marker(latlng, { icon: createSatelliteIcon(satellites[satid]) }).addTo(map);
                    marker.bindPopup(createPopupContent(satellites[satid], position));
                    marker.on('click', () => fetchDetailedInfo(satid));
                    markers[satid] = marker;
                    initPathLine(satid, latlng);
                }

                // Fetch and update trajectory
                updateTrajectory(satid);
            })
            .catch(error => {
                console.error('Error updating satellite position:', satid, error);
                displayErrorMessage(`Error updating satellite position: ${error.message}`);
            });
    });
}

function createPopupContent(satellite, position) {
    return `
        <h3>${satellite.satname}</h3>
        <p>NORAD ID: ${satellite.satid}</p>
        <p>Int'l Designator: ${satellite.intDesignator}</p>
        <p>Launch Date: ${satellite.launchDate}</p>
        <p>Latitude: ${position.satlatitude.toFixed(4)}</p>
        <p>Longitude: ${position.satlongitude.toFixed(4)}</p>
        <p>Altitude: ${position.sataltitude.toFixed(2)} km</p>
        <div id="detailed-info-${satellite.satid}">
            <button onclick="fetchDetailedInfo(${satellite.satid})">Load Detailed Info</button>
        </div>
    `;
}

function fetchDetailedInfo(satid) {
    console.log('Fetching detailed info for satellite:', satid);
    fetch(`/api/satellite/${satid}/info`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received detailed info for satellite:', satid, data);
            updatePopupWithDetailedInfo(satid, data);
        })
        .catch(error => {
            console.error('Error fetching detailed satellite info:', satid, error);
            displayErrorMessage(`Error fetching detailed satellite info: ${error.message}`);
        });
}

function updatePopupWithDetailedInfo(satid, data) {
    const detailedInfoContainer = document.getElementById(`detailed-info-${satid}`);
    if (detailedInfoContainer) {
        detailedInfoContainer.innerHTML = `
            <h4>Detailed Information</h4>
            <p>TLE Line 1: ${data.tle.split('\r\n')[0]}</p>
            <p>TLE Line 2: ${data.tle.split('\r\n')[1]}</p>
        `;
    }
}

function initPathLine(satid, latlng) {
    console.log('Initializing path line for satellite:', satid);
    pathLines[satid] = L.polyline([latlng], {color: getRandomColor(), weight: 2, opacity: 0.5}).addTo(map);
}

function updatePathLine(satid, latlng) {
    if (pathLines[satid]) {
        console.log('Updating path line for satellite:', satid);
        const currentPath = pathLines[satid].getLatLngs();
        currentPath.push(latlng);
        pathLines[satid].setLatLngs(currentPath);
    }
}

function updateTrajectory(satid) {
    console.log('Updating trajectory for satellite:', satid);
    fetch(`/api/satellite/${satid}/trajectory?seconds=300`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received trajectory data for satellite:', satid, data);
            if (!data.positions || data.positions.length === 0) {
                console.error('No trajectory data received for satellite:', satid);
                return;
            }

            const trajectoryPoints = data.positions.map(pos => [pos.satlatitude, pos.satlongitude]);

            if (trajectoryLines[satid]) {
                console.log('Updating existing trajectory line for satellite:', satid);
                trajectoryLines[satid].setLatLngs(trajectoryPoints);
            } else {
                console.log('Creating new trajectory line for satellite:', satid);
                trajectoryLines[satid] = L.polyline(trajectoryPoints, {color: getRandomColor(), weight: 2, opacity: 0.7, dashArray: '5, 5'}).addTo(map);
            }
        })
        .catch(error => {
            console.error('Error updating satellite trajectory:', satid, error);
            displayErrorMessage(`Error updating satellite trajectory: ${error.message}`);
        });
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function fetchSatellites(category) {
    console.log('Fetching satellites for category:', category);
    fetch(`/api/satellites/${category}?limit=${satelliteLimit}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received raw satellite data:', JSON.stringify(data));
            if (data.above && data.above.length > 0) {
                console.log('Number of satellites received:', data.above.length);
                satellites = {};
                Object.keys(markers).forEach(satid => {
                    console.log('Removing existing marker for satellite:', satid);
                    map.removeLayer(markers[satid]);
                    delete markers[satid];
                });
                Object.keys(pathLines).forEach(satid => {
                    console.log('Removing existing path line for satellite:', satid);
                    map.removeLayer(pathLines[satid]);
                    delete pathLines[satid];
                });
                Object.keys(trajectoryLines).forEach(satid => {
                    console.log('Removing existing trajectory line for satellite:', satid);
                    map.removeLayer(trajectoryLines[satid]);
                    delete trajectoryLines[satid];
                });

                data.above.forEach(satellite => {
                    console.log('Adding satellite to tracking:', satellite.satname);
                    satellites[satellite.satid] = satellite;
                });

                updateSatellitePositions();
            } else {
                console.error('No satellite data received or empty data');
                displayErrorMessage('No satellite data received. Please try again later.');
            }
        })
        .catch(error => {
            console.error('Error fetching satellites:', error);
            displayErrorMessage(`Error fetching satellites: ${error.message}`);
        });
}

function populateCategories() {
    console.log('Populating categories');
    const categorySelect = document.getElementById('category');
    fetch('/api/categories')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(categories => {
            console.log('Received categories:', categories);
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching categories:', error);
            displayErrorMessage(`Error fetching categories: ${error.message}`);
        });
}

function displayErrorMessage(message) {
    const errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        const newErrorContainer = document.createElement('div');
        newErrorContainer.id = 'error-container';
        newErrorContainer.style.color = 'red';
        newErrorContainer.style.padding = '10px';
        newErrorContainer.style.margin = '10px 0';
        newErrorContainer.style.backgroundColor = '#ffeeee';
        newErrorContainer.style.border = '1px solid #ff0000';
        document.getElementById('app').prepend(newErrorContainer);
    }
    document.getElementById('error-container').textContent = message;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');
    initMap();
    populateCategories();
    
    const categorySelect = document.getElementById('category');
    categorySelect.addEventListener('change', (event) => {
        fetchSatellites(event.target.value);
    });

    const limitInput = document.getElementById('satellite-limit');
    limitInput.addEventListener('change', (event) => {
        satelliteLimit = parseInt(event.target.value) || 5;
        fetchSatellites(categorySelect.value);
    });

    fetchSatellites(0);
    setInterval(updateSatellitePositions, config.updateInterval);
});
