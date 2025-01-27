import { getTodaysTrips } from "./scripts/trips";
import { useEffect } from "react";

export const Test = () => {
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        console.log("Fetching trips...");
        const trips = await getTodaysTrips();
        console.log(trips);
      } catch (error) {
        console.error("Error fetching trips:", error);
      }
    };

    fetchTrips();
  }, []);

  return (
    <>
      <p> Test Component</p>
      <p> Results in console » </p>
    </>
  );
};
