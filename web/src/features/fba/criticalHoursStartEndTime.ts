import { FireZoneFuelStats } from '@/api/fbaAPI'
import { isNil, isUndefined } from 'lodash'

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
  minStartTime: number | undefined
  maxEndTime: number | undefined
} => {
  let minStartTime: number | undefined = undefined
  let maxEndTime: number | undefined = undefined

  for (const fuel of fuels) {
    let { start_time, end_time } = fuel.critical_hours

    // Handle case where end_time is past midnight (e.g. 7 is later than 23).
    // Critical hours start_time can't be earlier than 0700, and the end time can't be later than 0700 the following day
    if (!isUndefined(start_time) && !isUndefined(end_time)) {
      if (end_time <= start_time) {
        end_time += 24
      }
    }

    if (!isUndefined(start_time)) {
      if (isUndefined(minStartTime) || start_time < minStartTime) {
        minStartTime = start_time
      }
    }

    if (!isUndefined(end_time)) {
      if (isUndefined(maxEndTime) || end_time > maxEndTime) {
        maxEndTime = end_time
      }
    }
  }
  if (!isNil(maxEndTime)) {
    maxEndTime = maxEndTime % 24 // normalize back to 24 hour clock
  }

  return { minStartTime, maxEndTime }
}
