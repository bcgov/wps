import { FireZoneFuelStats } from '@/api/fbaAPI'
import { isUndefined } from 'lodash'

/**
 *
 *
 * @param fuels FireZoneFuelStats[]
 * @returns
 */
export function getMinStartAndMaxEndTime(fuels: FireZoneFuelStats[]): {
  minStartTime: number | undefined
  maxEndTime: number | undefined
} {
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
  if (!isUndefined(maxEndTime)) {
    maxEndTime = maxEndTime % 24 // normalize back to 24 hour clock
  }

  return { minStartTime, maxEndTime }
}
