// IMPORTS
import { Trip, getTodaysTrips } from "./scripts/trips";
import { useState, useEffect } from "react";

// COMPONENT
export const ScheduleGrid = () => {
  // State
  const [trips, setTrips] = useState<Trip[]>([]); // list of trips
  const [loading, setLoading] = useState(true); // loading state
  const [error, setError] = useState<string | null>(null); // error message

  // Fetch data
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const data = await getTodaysTrips(); // Fetch trips from the API
        const trips = data.all_trips;
        console.log(trips);
        setTrips(trips); // Update the trips state
        setError(null); // Clear previous errors
      } catch (err) {
        setError("Failed to load schedule."); // Set error message
      } finally {
        setLoading(false); // Done loading
      }
    };
    fetchTrips();

    // Separate trips from Swan's Island and trips from bass Harbor.
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
    <div>
      <h1>Today's Ferry Schedule</h1>
      <h3>Swan's Island</h3>
      <h3>Bass Harbor</h3>
      {trips.map((trip) => (
        <>
          <p>{trip.departure_time}</p>
        </>
      ))}
    </div>
  );
};
