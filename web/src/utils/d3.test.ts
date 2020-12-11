import { getNearestByDate, getTickValues } from 'utils/d3'
import { PDT_UTC_OFFSET, PST_UTC_OFFSET } from './constants'

describe('d3 util functions', () => {
  describe('getNearestByDate', () => {
    it('should return the nearest date in the given array', () => {
      const dates = [
        { date: new Date('2020-11-25T12:00:00+00:00') },
        { date: new Date('2020-11-25T15:00:00+00:00') }
      ]
      expect(getNearestByDate(new Date('2020-11-25T12:00:00+00:00'), dates)).toEqual(dates[0]) // prettier-ignore
      expect(getNearestByDate(new Date('2020-11-25T13:00:00+00:00'), dates)).toEqual(dates[0]) // prettier-ignore
      expect(getNearestByDate(new Date('2020-11-25T13:30:00+00:00'), dates)).toEqual(dates[0]) // prettier-ignore
      expect(getNearestByDate(new Date('2020-11-25T14:00:00+00:00'), dates)).toEqual(dates[1]) // prettier-ignore
      expect(getNearestByDate(new Date('2020-11-25T15:00:00+00:00'), dates)).toEqual(dates[1]) // prettier-ignore
    })
  })

  describe('getTickValues', () => {
    it('should return the correct date array based on the given arguments', () => {
      const d1 = new Date('2020-11-28T12:00:00+00:00')
      const d2 = new Date('2020-11-30T12:00:00+00:00')
      const d3 = new Date('2020-12-15T12:00:00+00:00')
      const d4 = new Date('2020-12-25T12:00:00+00:00')

      expect(getTickValues([undefined, undefined], PDT_UTC_OFFSET)).toEqual([])
      expect(getTickValues([d1, d2], PDT_UTC_OFFSET)).toEqual([
        new Date('2020-11-29T07:00:00+00:00'),
        new Date('2020-11-30T07:00:00+00:00')
      ])
      expect(getTickValues([d1, d2], PST_UTC_OFFSET)).toEqual([
        new Date('2020-11-29T08:00:00+00:00'),
        new Date('2020-11-30T08:00:00+00:00')
      ])
      expect(getTickValues([d1, d3], PST_UTC_OFFSET)).toHaveLength(17)
      expect(getTickValues([d1, d3], PST_UTC_OFFSET, true)).toHaveLength(9)
      expect(getTickValues([d1, d4], PST_UTC_OFFSET, true)).toHaveLength(9)
    })

    it('should return the correct date array in any case', () => {
      const d1 = new Date('2020-11-28T12:00:00+00:00')
      const d1NextMonth = new Date('2020-12-01T12:00:00+00:00')
      const d2 = new Date('2020-12-31T12:00:00+00:00')
      const d2NextYear = new Date('2021-01-02T12:00:00+00:00')

      expect(getTickValues([d1, d1NextMonth], PDT_UTC_OFFSET)).toEqual([
        new Date('2020-11-29T07:00:00+00:00'),
        new Date('2020-11-30T07:00:00+00:00'),
        new Date('2020-12-01T07:00:00+00:00')
      ])
      expect(getTickValues([d2, d2NextYear], PDT_UTC_OFFSET)).toEqual([
        new Date('2021-01-01T07:00:00+00:00'),
        new Date('2021-01-02T07:00:00+00:00')
      ])
    })
  })
})
