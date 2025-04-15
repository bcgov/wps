import { FireZoneFuelStats } from '@/api/fbaAPI'
import { isNil } from 'lodash'

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

    // Handle case where end_time is past midnight by adding 24 hours if the end_time <= start time.
    // Critical hours start_time can't be earlier than 0700, and the end time can't be later than 0700 the following day
    if (!isNil(start_time) && !isNil(end_time)) {
      if (criticalHoursExtendToNextDay(start_time, end_time)) {
        end_time += 24
      }
    }

    if (!isNil(start_time)) {
      if (isNil(minStartTime) || start_time < minStartTime) {
        minStartTime = start_time
      }
    }

    if (!isNil(end_time)) {
      if (isNil(maxEndTime) || end_time > maxEndTime) {
        maxEndTime = end_time
      }
    }
  }
  if (!isNil(maxEndTime)) {
    maxEndTime = maxEndTime % 24 // normalize back to 24 hour clock
  }

  return { minStartTime, maxEndTime }
}

const criticalHoursExtendToNextDay = (startTime: number, endTime: number): boolean => {
  const extendsNextDay = endTime <= startTime && endTime < 8 // critical hours can't extend into the next day past 07:00
  return extendsNextDay
}

export const formatCriticalHoursTimeText = (startTime: number, endTime: number): string[] => {
  const extendsNextDay = criticalHoursExtendToNextDay(startTime, endTime)

  const paddedMinStartTime = String(startTime).padStart(2, '0')
  const paddedMaxEndTime = String(endTime).padStart(2, '0')
  const formattedStartTime = `${paddedMinStartTime}:00`
  const formattedEndTime = `${paddedMaxEndTime}:00${extendsNextDay ? '+1' : ''}`

  return [formattedStartTime, formattedEndTime]
}
