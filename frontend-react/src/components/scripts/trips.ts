export interface Trip {
  // Define the structure of a trip based on API response
  id: number;
  routeID: number;
  departureime: string;
  arrivalTime: string;
  originating_stop: {
    stop_id: number;
  };
}

/**
 * Fetches all trips from the current day.
 * @returns Trip[]
 */
export async function getTodaysTrips(): Promise<Trip[]> {
  const response = await fetch("http://127.0.0.1:8000/routes/1000");
  const todaysTrips = await response.json();
  return todaysTrips;
}

/**
 * Filter trips by origin.
 * @param trips » list of all trips from all port origins.
 * @param origin_id » desired port of origin to filter for.
 * @returns tripsFromPort » list of trips from the specified port.
 */
export function sortTripsByOrigin(trips: Trip[], origin_id: number): Trip[] {
  const tripsFromPort: Trip[] = [];

  for (let i = 0; i < trips.length; i++) {
    // For every trip in the array of trips
    const portOfOrigin = trips[i].originating_stop.stop_id;
    // If from Swan's Island -> add to tripsFromSwansIsland
    if (portOfOrigin == origin_id) {
      tripsFromPort.push(trips[i]);
    }
  }
  return tripsFromPort;
}
