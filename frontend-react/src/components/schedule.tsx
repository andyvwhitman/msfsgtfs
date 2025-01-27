// IMPORTS
import { useState, useEffect } from "react";
import { Trip, getTodaysTrips, sortTripsByOrigin } from "./scripts/trips.ts";

export const ScheduleGrid = () => {

  };

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
