export const stationCodeQueryKey = 'codes'

export const getStationCodesFromUrl = (search: string): number[] => {
  const codeQueryString = new URLSearchParams(search).get(stationCodeQueryKey)
  const stationCodes = codeQueryString
    ? codeQueryString
        .split(',')
        .map(code => Number(code))
        .filter(code => Boolean(code))
    : []

  return stationCodes
}
