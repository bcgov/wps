import { COMPARED_YEAR_COLOURS, chooseComparedYears, MAX_COMPARED_YEARS, yearsBefore } from './comparedYears'

const [first, second, third] = COMPARED_YEAR_COLOURS

describe('chooseComparedYears', () => {
  it('gives each year a colour, newest first', () => {
    expect(chooseComparedYears([], [2017, 2023])).toEqual([
      { year: 2023, colour: second },
      { year: 2017, colour: first }
    ])
  })

  it('keeps the colours of the years left when one is removed', () => {
    const current = chooseComparedYears([], [2023, 2021, 2017])

    expect(chooseComparedYears(current, [2021, 2017])).toEqual([
      { year: 2021, colour: second },
      { year: 2017, colour: third }
    ])
  })

  it('gives a new year the colour that is free', () => {
    const current = chooseComparedYears(chooseComparedYears([], [2023, 2021]), [2021])

    expect(chooseComparedYears(current, [2021, 2003])).toEqual([
      { year: 2021, colour: second },
      { year: 2003, colour: first }
    ])
  })

  it('leaves out years past the most that can be compared', () => {
    const years = [2025, 2024, 2023, 2022, 2021, 2020]

    expect(chooseComparedYears([], years).map(({ year }) => year)).toEqual(years.slice(0, MAX_COMPARED_YEARS))
  })
})

describe('yearsBefore', () => {
  it('counts back from the year', () => {
    expect(yearsBefore(2026, 3, 1987)).toEqual([2025, 2024, 2023])
  })

  it('stops at the first year', () => {
    expect(yearsBefore(1989, 5, 1987)).toEqual([1988, 1987])
  })
})
