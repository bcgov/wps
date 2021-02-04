import moment from 'moment'

import { formatDateInISO } from 'utils/date'

export const stationCodeQueryKey = 'codes'
export const timeOfInterestQueryKey = 'toi'

export const getTimeOfInterestFromUrl = (search: string): string => {
  const queryString = new URLSearchParams(search).get(timeOfInterestQueryKey)

  if (queryString && moment(queryString).isValid()) {
    return queryString
  }

  return formatDateInISO(new Date())
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
