import { DateTime } from 'luxon'
import { formatISODateInPST, formatMonthAndDay, toBCPacificTime } from './date'

describe('Date util functions', () => {
  describe('toBCPacificTime', () => {
    it.each([
      ['2024-01-15T07:30:00Z', '2024-01-14T23:30:00-08:00'],
      ['2024-07-15T07:30:00Z', '2024-07-15T00:30:00-07:00'],
      ['2026-11-01T09:30:00Z', '2026-11-01T02:30:00-07:00'],
      ['2027-01-15T07:30:00Z', '2027-01-15T00:30:00-07:00']
    ])('converts %s to Pacific time without changing the instant', (instant, expected) => {
      const original = DateTime.fromISO(instant, { zone: 'utc' })

      const result = toBCPacificTime(original)

      expect(result.toISO({ suppressMilliseconds: true })).toBe(expected)
      expect(result.toMillis()).toBe(original.toMillis())
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
})
