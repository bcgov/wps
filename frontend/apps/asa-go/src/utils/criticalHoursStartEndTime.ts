import { FireZoneFuelStats } from "@/api/fbaAPI";
import { isNil } from "lodash";

/**
 * Function to calculate the minimum start and maximum end time for critical hours.
 * Critical hours can start as early as 0700 and continue on to the next day at 0700.
 * Because of this we need some logic to determine the maximum time.
 * ie. 0600 the following day needs to be considered later than 2300 the same day.
 *
 * @param fuels FireZoneFuelStats[]
 * @returns
 */
export const getMinStartAndMaxEndTime = (
  fuels: FireZoneFuelStats[]
): {
  minStartTime: number | undefined;
  maxEndTime: number | undefined;
  duration: number | undefined;
} => {
  let minStartTime: number | undefined = undefined;
  let maxEndTime: number | undefined = undefined;
  let duration: number | undefined = undefined;

  for (const fuel of fuels) {
    const startTime = fuel.critical_hours.start_time;
    let endTime = fuel.critical_hours.end_time;

    // Handle case where end_time is past midnight by adding 24 hours if the end_time <= start time.
    // Critical hours start_time can't be earlier than 0700, and the end time can't be later than 0700 the following day
    if (!isNil(startTime) && !isNil(endTime)) {
      if (criticalHoursExtendToNextDay(startTime, endTime)) {
        endTime += 24;
      }
    }

    if (!isNil(startTime)) {
      if (isNil(minStartTime) || startTime < minStartTime) {
        minStartTime = startTime;
      }
    }

    if (!isNil(endTime)) {
      if (isNil(maxEndTime) || endTime > maxEndTime) {
        maxEndTime = endTime;
      }
    }
  }

  if (!isNil(minStartTime) && !isNil(maxEndTime)) {
    duration = maxEndTime - minStartTime;
  }

  if (!isNil(maxEndTime)) {
    maxEndTime = maxEndTime % 24; // normalize back to 24 hour clock
  }

  return { minStartTime, maxEndTime, duration };
};

export const criticalHoursExtendToNextDay = (
  startTime: number,
  endTime: number
): boolean => {
  const extendsNextDay = endTime <= startTime && endTime < 8; // critical hours can't extend into the next day past 07:00
  return extendsNextDay;
};

export const formatCriticalHoursTimeText = (
  startTime: number,
  endTime: number,
  shorthand: boolean = true
): string[] => {
  const extendsNextDay = criticalHoursExtendToNextDay(startTime, endTime);

  let endSuffix = "";
  if (extendsNextDay) {
    endSuffix = shorthand ? ' (+1 day)' : ' tomorrow'
  }

  const formatHour = (hour: number, shorthand: boolean) => {
    if (shorthand) {
      return `${String(hour).padStart(2, '0')}`
    }
    return `${String(hour).padStart(2, '0')}:00`
  }

  return [formatHour(startTime, shorthand), `${formatHour(endTime, shorthand)}${endSuffix}`];
};
