
// Listen for the DOM to finish loading?
document.addEventListener('DOMContentLoaded', () => {
    // Get all the data from the api
    fetch('http://127.0.0.1:5000/trips/1501')
        .then(response => response.json())
        .then(data => {
            console.log(data)

            // Parse data into a sensible schema
            let tripInfo = {
                time_start: data.departure_time,
                time_end: data.arrival_time,
                origin: data.originating_stop.stop_name,
                destination: data.destination_stop.stop_name
            }


            // Inject data from local schema to appropriate html objects
            let currentTripContainer = document.getElementById('current-trip-container');
            currentTripContainer.innerHTML = `<pre>${JSON.stringify(tripInfo, null, 4)}</pre>`;
            console.log(currentTripContainer)
        })
        // Handle errors
        .catch(error => {
            console.error('Error', error);
        })


});