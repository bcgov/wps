export const getStationCodesFromUrl = (search: string) => {
  const codeQueryString = new URLSearchParams(search).get('code')
  const stationCodes = codeQueryString
    ? codeQueryString
        .split(',')
        .map(code => Number(code))
        .filter(code => Boolean(code))
    : []

  return stationCodes
}
