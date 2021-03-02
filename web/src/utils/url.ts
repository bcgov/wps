import moment from 'moment'
import { PST_UTC_OFFSET } from './constants'

import { formatDateInISO } from './date'

export const stationCodeQueryKey = 'codes'
export const timeOfInterestQueryKey = 'toi'

export const getTimeOfInterestFromUrl = (search: string): string => {
  const queryString = new URLSearchParams(search).get(timeOfInterestQueryKey)

  if (queryString && moment(queryString).isValid()) {
    return queryString
  }

  const currentDateInPST = moment()
    .utcOffset(PST_UTC_OFFSET)
    .toDate()

  return formatDateInISO(currentDateInPST)
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
