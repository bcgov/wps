import { DateTime } from 'luxon'

import { PST_UTC_OFFSET } from './constants'
import { suppressMilliInISO } from './date'

export const stationCodeQueryKey = 'codes'
export const timeOfInterestQueryKey = 'toi'

export const getTimeOfInterestFromUrl = (search: string): string => {
  const queryString = new URLSearchParams(search).get(timeOfInterestQueryKey)
  let datetime = null

  if (queryString && DateTime.fromISO(queryString).isValid) {
    datetime = DateTime.fromISO(queryString)
  } else {
    datetime = DateTime.fromObject({ second: 0 })
  }

  const iso = datetime.setZone(`UTC${PST_UTC_OFFSET}`).toISO()

  return suppressMilliInISO(iso)
}

export const getStationCodesFromUrl = (search: string): number[] => {
  const queryString = new URLSearchParams(search).get(stationCodeQueryKey)
  const stationCodes = queryString // ex. 322,838
    ? queryString
        .split(',')
        .map(code => Number(code))
        .filter(code => Boolean(code))
    : []

  return stationCodes
}
