import { stationCodeQueryKey, getStationCodesFromUrl } from 'utils/url'

describe('Url util functions', () => {
  describe('getStationCodesFromUrl', () => {
    it('should return the correct wx station codes based on the given query', () => {
      expect(getStationCodesFromUrl('')).toEqual([])
      expect(getStationCodesFromUrl('?some-random-key=')).toEqual([])
      expect(getStationCodesFromUrl(`?${stationCodeQueryKey}=`)).toEqual([])
      expect(getStationCodesFromUrl(`?${stationCodeQueryKey}=123, null, undefined`)).toEqual([123]) // prettier-ignore
      expect(getStationCodesFromUrl(`?${stationCodeQueryKey}=123,456`)).toEqual([123, 456]) // prettier-ignore
    })
  })
})
