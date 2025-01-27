export interface Trip {
  arrival_time: string;
  departure_time: string;
  destination_stop: {
    stop_desc: string;
    stop_id: string;
    stop_lat: number;
    stop_lon: number;
    stop_name: string;
  };
  direction_id: number;
  originating_stop: {
    stop_desc: string;
    stop_id: string;
    stop_lat: number;
    stop_lon: number;
    stop_name: string;
  };
  route_id: string;
  trip_headsign: string;
  trip_id: string;
}

/**
 * Fetches all trips from the current day.
 * @returns Trip[]
 */
export async function getTodaysTrips(): Promise<Trip[]> {
  const response = await fetch("http://127.0.0.1:8000/routes/1000/today");
  if (!response.ok) throw new Error("Failed to fetch trips");
  return response.json();
}
