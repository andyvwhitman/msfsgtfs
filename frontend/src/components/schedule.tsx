// IMPORTS
import { Trip, getTodaysTrips } from "./scripts/trips";
import convertTime from "./scripts/convertTime";
import { useState, useEffect } from "react";
import "./styles/schedule.css";

// COMPONENT
export const Schedule = () => {
  // State
  const [trips, setTrips] = useState<Trip[]>([]); // list of trips
  const [swansIslandTrips, setSwansIslandTrips] = useState<Trip[]>([]);
  const [bassHarborTrips, setBassHarborTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true); // loading state
  const [error, setError] = useState<string | null>(null); // error message

  // Fetch data
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const data = await getTodaysTrips(); // Fetch trips from the API
        const trips = data.all_trips;
        console.log("all_trips", trips);
        // Separate trips from Swan's Island and trips from bass Harbor.
        const swansIslandTrips = trips.filter(
          (trip) => trip.originating_stop.stop_id === "1001",
        );
        const bassHarborTrips = trips.filter(
          (trip) => trip.originating_stop.stop_id === "1002",
        );
        console.log("swansIslandTrips: ", swansIslandTrips);
        console.log("bassHarborTrips: ", bassHarborTrips);

        // Set state
        setTrips(trips); // Update the trips state
        setSwansIslandTrips(swansIslandTrips);
        setBassHarborTrips(bassHarborTrips);
        setError(null); // Clear previous errors
      } catch (err) {
        setError("Failed to load schedule."); // Set error message
      } finally {
        setLoading(false); // Done loading
      }
    };
    fetchTrips();
  }, []); // Empty dependency array » runs only once

  // Handle loading and error states
  if (loading) {
    return <div>Loading schedule...</div>; // Show loading message
  }

  if (error) {
    return <div className="error">{error}</div>; // Show error message
  }

  // Main Render
  return (
    <div id="schedule">
      <div id="swans-island-schedule">
        <h3>Swan's Island</h3>
        {swansIslandTrips.map((trip) => (
          <p>{convertTime(trip.departure_time)}</p>
        ))}
      </div>
      <div id="bass-harbor-schedule">
        <h3>Bass Harbor</h3>
        {bassHarborTrips.map((trip) => (
          <p>{convertTime(trip.departure_time)}</p>
        ))}
      </div>
    </div>
  );
};
