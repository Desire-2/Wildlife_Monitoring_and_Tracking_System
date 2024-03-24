document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('update_data', function(data) {
        console.log('Received data:', data);
        // Update map markers with received data
        var marker = L.marker([data.latitude, data.longitude]).addTo(map);
        marker.bindPopup('Wildlife ID: ' + data.animal_id).openPopup();
    });

    // Function to clear all markers from the map
    function clearMapMarkers() {
        map.eachLayer(function (layer) {
            if (layer instanceof L.Marker) {
                map.removeLayer(layer);
            }
        });
    }

    // Button click event handler to clear all markers from the map
    document.getElementById('clear-map').addEventListener('click', function () {
        clearMapMarkers();
    });
});
