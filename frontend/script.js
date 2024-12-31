function convertTime(timeStr) {
    let [hours, minutes] = timeStr.split(':');
    hours = parseInt(hours);
    const period = hours >= 12 ? 'PM' : 'AM';

    // Convert to 12-hour format
    hours = hours % 12;
    hours = hours ? hours : 12;

    // Add space if single digit
    const hourStr = hours < 10 ? ' ' + hours : hours;

    return `${hourStr}:${minutes} ${period}`;
}

// Listen for the DOM to finish loading?
document.addEventListener('DOMContentLoaded', () => {
    // Get all the data from the api
    fetch('http://127.0.0.1:5000/trips/1101')
        .then(response => response.json())
        .then(data => {
            console.log(data)

            // Parse data into a sensible schema
            let tripInfo = {
                time_start: convertTime(data.departure_time),
                time_end: convertTime(data.arrival_time),
                origin: data.originating_stop.stop_name,
                destination: data.destination_stop.stop_name
            }


            // Inject data from local schema to appropriate html objects

            // CURRENT FERRY

                // DEPARTURE TIME 
                document.getElementById('current-time').innerHTML = tripInfo.time_start;
                document.getElementById('location-from').innerHTML = tripInfo.origin;
                document.getElementById('location-to').innerHTML = tripInfo.destination;
                
                
        })
        // Handle errors
        .catch(error => {
            console.error('Error', error);
        })


});