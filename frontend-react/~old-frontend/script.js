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

async function getTodaysTrips() {
    const response = await fetch('http://127.0.0.1:5000/routes/1000');
    const todaysTrips = await response.json();
    return todaysTrips;
}

function sortTripsByOrigin(trips, origin_id) {
    let tripsFromPort = []

    for (let i = 0; i < trips.length; i++) {
        // For every trip in the array of trips
        let portOfOrigin = trips[i].originating_stop.stop_id
        // If from Swan's Island -> add to tripsFromSwansIsland
        if (portOfOrigin == origin_id) {
            tripsFromPort.push(trips[i])
        }
    }
    return tripsFromPort;
}


// Listen for the DOM to finish loading.
document.addEventListener('DOMContentLoaded', async () => {
    // Load today's date
    const currentDate = new Date();
    document.getElementById('header-date').textContent = currentDate.toLocaleDateString();

    // Fetch all trips for the day.
    let data = await getTodaysTrips();
    let active_trip = data.active_trip;
    let next_trip = data.next_trip;
    let all_trips = data.all_trips;

    // Trips separated by Swan's Island / Bass Harbor.
    let tripsFromSwansIsland = sortTripsByOrigin(all_trips, '1001');
    let tripsFromBassHarbor = sortTripsByOrigin(all_trips, '1002');
    
    const dataContainer = document.createElement('div');

    // Render trips from SWAN'S ISLAND in the LEFT COLUMN
    tripsFromSwansIsland.forEach(trip => {
        const tripDiv = document.createElement('div');
        tripDiv.className = 'left-column'
        tripDiv.textContent = `${convertTime(trip.departure_time)}`;
        tripDiv.setAttribute('data-cell', '');
        dataContainer.appendChild(tripDiv);
    })
    
    // Render trips from BASS HARBOR in the RIGHT COLUMN
    tripsFromBassHarbor.forEach(trip => {
        const tripDiv2 = document.createElement('div');
        tripDiv2.className = 'right-column'
        tripDiv2.textContent = `${convertTime(trip.departure_time)}`;
        tripDiv2.setAttribute('data-cell', '');
        dataContainer.appendChild(tripDiv2);
    })

    
    document.getElementById('schedule-grid').appendChild(dataContainer);


}); 



// Render the active trip in the card at the top.