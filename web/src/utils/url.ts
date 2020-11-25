export const stationCodeQueryKey = 'codes'

export const getStationCodesFromUrl = (search: string) => {
  const codeQueryString = new URLSearchParams(search).get('codes')
  const stationCodes = codeQueryString
    ? codeQueryString
        .split(',')
        .map(code => Number(code))
        .filter(code => Boolean(code))
    : []

  return stationCodes
}
