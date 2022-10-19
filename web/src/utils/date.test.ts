import {
  isNoonInPST,
  formatDatetimeInPST,
  formatMonthAndDay,
  formatDateInUTC00Suffix,
  formatISODateInPST
} from 'utils/date'

describe('Date util functions', () => {
  describe('isNoonInPST', () => {
    it('should check if the give datetime is PST noon', () => {
      expect(isNoonInPST('2020-11-25T19:00:00+00:00')).toEqual(false)
      expect(isNoonInPST('2020-11-25T20:00:00+00:00')).toEqual(true)
      expect(isNoonInPST('2020-11-25T21:00:00+00:00')).toEqual(false)
      expect(isNoonInPST('2020-11-26T20:00:00+00:00')).toEqual(true)
    })
  })

  describe('formatDateTimeInPST', () => {
    it("should format the given date in 'YYYY-MM-DD HH:mm'", () => {
      expect(formatDatetimeInPST('2020-11-24T20:00:00+00:00')).toEqual('2020-11-24 12:00')
      expect(formatDatetimeInPST('2020-11-25T20:00:00+00:00')).toEqual('2020-11-25 12:00')
      const d = new Date('2020-11-25T20:00:00+00:00')
      expect(formatDatetimeInPST(d)).toEqual('2020-11-25 12:00')
    })

    it('should format the given date based on the given format', () => {
      expect(formatDatetimeInPST('2020-11-25T20:00:00+00:00', 'yyyy-MM-dd')).toEqual('2020-11-25')
      expect(formatDatetimeInPST('2020-11-25T20:00:00+00:00', 'yyyy-MM-dd HH')).toEqual('2020-11-25 12')
      const d = new Date('2020-11-25T20:00:00+00:00')
      expect(formatDatetimeInPST(d, 'yyyy-MM-dd')).toEqual('2020-11-25')
    })
  })

  describe('formatDateInPST', () => {
    it('should format the date with PST timezone', () => {
      const datetime = formatISODateInPST('2021-08-02T00:00-08:00')
      expect(datetime.year).toBe(2021)
      expect(datetime.month).toBe(8)
      expect(datetime.day).toBe(2)
      expect(datetime.toFormat('yyyy-MM-dd')).toBe('2021-08-02')
    })
  })

  describe('formatMonthAndDay', () => {
    it("should format the given month and date in 'D MMMM'", () => {
      expect(formatMonthAndDay(1, 1)).toEqual('1 January')
      expect(formatMonthAndDay(1, 10)).toEqual('10 January')
      expect(formatMonthAndDay(4, 15)).toEqual('15 April')
      expect(formatMonthAndDay(9, 30)).toEqual('30 September')
    })
  })

  describe('formatDateInUTC00Suffix', () => {
    it('should return the noon date time', () => {
      expect(formatDateInUTC00Suffix('2021-04-26T00:37:00-08:00')).toEqual('2021-04-26T20:00:00+00:00')
      expect(formatDateInUTC00Suffix('2021-04-26T08:37:00-08:00')).toEqual('2021-04-26T20:00:00+00:00')
      expect(formatDateInUTC00Suffix('2021-04-26T17:37:00-08:00')).toEqual('2021-04-26T20:00:00+00:00')
      expect(formatDateInUTC00Suffix('2021-04-26T23:37:00-08:00')).toEqual('2021-04-26T20:00:00+00:00')
    })
  })
})
