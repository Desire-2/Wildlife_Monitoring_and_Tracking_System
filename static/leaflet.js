document.addEventListener('DOMContentLoaded', function () {
    // Initialize the map with a specific center and zoom level
    var map = L.map('map').setView([51.505, -0.09], 13);

    // Add a tile layer from OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Connect to the server using Socket.IO
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    // Log a message when connected to the server
    socket.on('connect', function() {
        console.log('Connected to server');
    });

    // Receive real-time updates from the server and add markers to the map
    socket.on('update_data', function(data) {
        console.log('Received data:', data);
        // Add a marker at the received coordinates with a popup showing the wildlife ID
        var marker = L.marker([data.latitude, data.longitude]).addTo(map);
        marker.bindPopup('Wildlife ID: ' + data.animal_id).openPopup();
    });
});
