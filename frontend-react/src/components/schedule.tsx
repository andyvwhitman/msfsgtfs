// IMPORTS
import { useState, useEffect } from "react";
import { Trip, getTodaysTrips, sortTripsByOrigin } from "./scripts/trips.ts";

export const ScheduleGrid = () => {
  // State
  const [trips, setTrips] = useState<Trip[]>([]);

  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const data = await getTodaysTrips();
        setTrips(data);
      } catch (error) {
        console.error("Error fetching trips:", error);
      }
    };
    fetchTrips();
  });

  return (
    <div>
      {trips.map((trip) => (
        <p key={trip.id}>
          Trip {trip.id}: {trip.departureTime} → {trip.arrivalTime}
        </p>
      ))}
    </div>
  );
};
