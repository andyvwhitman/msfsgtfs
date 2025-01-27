/**
 * Converts a time string from 24-Hour time to 12-Hour time
 * @param timeStr: string » (HH:mm)
 * @returns timeStr: string » (hh:mm a)
 */
export default function convertTime(timeStr: string): string {
  const [hours, minutes] = timeStr.split(":");
  let parsedHours = parseInt(hours, 10);
  const period = parsedHours >= 12 ? "PM" : "AM";

  // Convert to 12-hour format
  parsedHours = parsedHours % 12;
  parsedHours = parsedHours ? parsedHours : 12;

  // Add space if single digit
  const hourStr = parsedHours < 10 ? ` ${parsedHours}` : parsedHours.toString();

  return `${hourStr}:${minutes} ${period}`;
}
