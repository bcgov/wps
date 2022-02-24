import { DateTime } from 'luxon'
import {
  isNoonInPST,
  formatDatetimeInPST,
  formatMonthAndDay,
  formatDateInUTC00Suffix,
  getPrepWeeklyDateRange,
  getPrepDailyDateRange,
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
      expect(formatDatetimeInPST('2020-11-25T20:00:00+00:00', 'yyyy-MM-dd')).toEqual(
        '2020-11-25'
      )
      expect(formatDatetimeInPST('2020-11-25T20:00:00+00:00', 'yyyy-MM-dd HH')).toEqual(
        '2020-11-25 12'
      )
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
      expect(datetime.zone.name).toBe('America/Vancouver')
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
      expect(formatDateInUTC00Suffix('2021-04-26T00:37:00-08:00')).toEqual(
        '2021-04-26T20:00:00+00:00'
      )
      expect(formatDateInUTC00Suffix('2021-04-26T08:37:00-08:00')).toEqual(
        '2021-04-26T20:00:00+00:00'
      )
      expect(formatDateInUTC00Suffix('2021-04-26T17:37:00-08:00')).toEqual(
        '2021-04-26T20:00:00+00:00'
      )
      expect(formatDateInUTC00Suffix('2021-04-26T23:37:00-08:00')).toEqual(
        '2021-04-26T20:00:00+00:00'
      )
    })
  })

  describe('Prep start and end days', () => {
    const monday = DateTime.fromISO('2021-10-04T06:30:00') //=> Mon, Oct 4, 2021 at 6:30
    const tuesday = DateTime.fromISO('2021-10-05T06:30:00') //=> Tue, Oct 5, 2021 at 6:30
    const wednesday = DateTime.fromISO('2021-10-06T06:30:00') //=> Wed, Oct 6, 2021 at 6:30
    const thursday = DateTime.fromISO('2021-10-07T06:30:00') //=> Thu, Oct 7, 2021 at 6:30
    const friday = DateTime.fromISO('2021-10-08T06:30:00') //=> Fri, Oct 8, 2021 at 6:30
    const saturday = DateTime.fromISO('2021-10-09T06:30:00') //=> Sat, Oct 9, 2021 at 6:30
    const sunday = DateTime.fromISO('2021-10-10T06:30:00') //=> Sun, Oct 10, 2021 at 6:30

    it('should return start, end of given day for daily range', () => {
      const expected = {
        start: monday.startOf('day'),
        end: monday.endOf('day')
      }
      expect(getPrepDailyDateRange(monday.toISO())).toEqual(expected)
    })

    describe('weekly prep days', () => {
      it('should return date of interest + 4 days when date of interest is Monday', () => {
        const expected = {
          start: monday.startOf('day'),
          end: monday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(monday.toISO())).toEqual(expected)
      })
      it('should return Mon-Tue and date of interest + 3 days, when date of interest is Tuesday', () => {
        const expected = {
          start: monday.startOf('day'),
          end: monday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(tuesday.toISO())).toEqual(expected)
      })
      it('should return Mon-Wed and date of interest + 2 days, when date of interest is Wed', () => {
        const expected = {
          start: monday.startOf('day'),
          end: monday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(wednesday.toISO())).toEqual(expected)
      })
      it('should return Thu (prep day) and date of interest + 4 days when date of interest is Thu', () => {
        const expected = {
          start: thursday.startOf('day'),
          end: thursday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(thursday.toISO())).toEqual(expected)
      })
      it('should return Thu-Fri and date of interest + 3 days when date of interest is Fri', () => {
        const expected = {
          start: thursday.startOf('day'),
          end: thursday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(friday.toISO())).toEqual(expected)
      })
      it('should return Thu-Sat and date of interest + 2 days when date of interest is Sat', () => {
        const expected = {
          start: thursday.startOf('day'),
          end: thursday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(saturday.toISO())).toEqual(expected)
      })
      it('should return Thu-Sun and date of interest + 1 days when date of interest is Sun', () => {
        const expected = {
          start: thursday.startOf('day'),
          end: thursday.startOf('day').plus({ days: 5 }).minus({ milliseconds: 1 })
        }
        expect(getPrepWeeklyDateRange(sunday.toISO())).toEqual(expected)
      })
    })
  })
})
