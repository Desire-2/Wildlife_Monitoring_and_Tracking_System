document.addEventListener("DOMContentLoaded", function () {
    var map = L.map("map").setView([0, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 100,
    }).addTo(map);

    var sightings = [
        { species: "Lion", location: [51.5, -0.09], date: "2024-02-25", habitat: "Savannah" },
        { species: "Elephant", location: [48.85, 2.35], date: "2024-02-26", habitat: "Forest" }
        // Add more sightings as needed
    ];

    // Add markers for wildlife sightings
    sightings.forEach(function(sighting) {
        var marker = L.marker(sighting.location).addTo(map);
        marker.bindPopup(`<b>${sighting.species}</b><br>Date: ${sighting.date}<br>Habitat: ${sighting.habitat}`).openPopup();
    });

    // Add event listener to wildlife sighting cards for map interaction
    document.querySelectorAll('.sighting-card').forEach(function(card) {
        card.addEventListener('click', function() {
            var species = card.querySelector('.card-title').textContent;
            var location = card.querySelector('.card-text').textContent.split(':')[1].trim();

            var sightingLocation = null;
            sightings.forEach(function(sighting) {
                if (sighting.species === species && sighting.location[0].toFixed(2) === location.split(',')[0].trim() && sighting.location[1].toFixed(2) === location.split(',')[1].trim()) {
                    sightingLocation = sighting.location;
                }
            });

            if (sightingLocation) {
                map.panTo(sightingLocation);
                L.marker(sightingLocation).addTo(map)
                    .bindPopup(`<strong>${species}</strong><br>${location}`)
                    .openPopup();
            } else {
                alert('Location not found for the selected sighting.');
            }
        });
    });
});
