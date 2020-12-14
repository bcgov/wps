import { getDatetimeComparator } from 'utils/table'

describe('Table util functions', () => {
  describe('getDatetimeComparator', () => {
    it('should return the correct compare function', () => {
      const ascending = getDatetimeComparator('asc')
      const descending = getDatetimeComparator('desc')
      const arr = [
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T20:00:00+00:00' },
        { datetime: '2020-12-09T22:00:00+00:00' }
      ]
      const deepCopy = JSON.parse(JSON.stringify(arr))

      expect([...arr].sort(ascending)).toEqual([
        { datetime: '2020-12-09T20:00:00+00:00' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T22:00:00+00:00' },
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' }
      ])

      expect([...arr].sort(descending)).toEqual([
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' },
        { datetime: '2020-12-09T22:00:00+00:00' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T20:00:00+00:00' }
      ])

      expect(arr).toEqual(deepCopy)
    })
  })
})
