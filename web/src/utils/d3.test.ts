import { getNearestByDate } from 'utils/d3'

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
})
