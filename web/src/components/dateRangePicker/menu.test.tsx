import { render } from '@testing-library/react'
import { format } from 'date-fns'
import Menu from 'components/dateRangePicker/Menu'
import { DateRange, NavigationAction, Setter } from 'components/dateRangePicker/types'
import { vi } from 'vitest'
import React from 'react'
/* eslint-disable @typescript-eslint/no-unused-vars */

const setup = (
  dateRange: DateRange,
  minDate: Date,
  maxDate: Date,
  inHoverRangeMock: (date: Date) => boolean,
  onDayClickMock: (date: Date) => void,
  onDayHoverMock: (date: Date) => void,
  onMonthNavigateMock: (marker: symbol, action: NavigationAction) => void,
  firstMonth: Date,
  setFirstMonthMock: Setter<Date>,
  secondMonth: Date,
  setSecondMonthMock: Setter<Date>,
  resetDateRangeMock: () => void
) => {
  const { getByTestId, getByRole } = render(
    <Menu
      dateRange={dateRange}
      minDate={minDate}
      maxDate={maxDate}
      helpers={{
        inHoverRange: inHoverRangeMock
      }}
      handlers={{
        onDayClick: onDayClickMock,
        onDayHover: onDayHoverMock,
        onMonthNavigate: onMonthNavigateMock,
        resetDateRange: resetDateRangeMock
      }}
      firstMonth={firstMonth}
      secondMonth={secondMonth}
      setFirstMonth={setFirstMonthMock}
      setSecondMonth={setSecondMonthMock}
    />
  )
  return { getByTestId, getByRole }
}
describe('Menu', () => {
  const startDate = new Date('2021/2/21')
  const endDate = new Date('2021/2/25')
  const firstMonth = new Date('2021/2/1')
  const secondMonth = new Date('2021/3/1')

  const inHoverRangeMock = vi.fn((date: Date): boolean => {
    return false
  })
  const onDayClickMock = vi.fn((date: Date): void => {
    /** no op */
  })
  const onDayHoverMock = vi.fn((date: Date): void => {
    /** no op */
  })
  const onMonthNavigateMock = vi.fn((marker: symbol, action: NavigationAction): void => {
    /** no op */
  })
  const setFirstMonthMock = vi.fn((date: Date): void => {
    /** no op */
  })
  const setSecondMonthMock = vi.fn((date: Date): void => {
    /** no op */
  })

  const resetDateRangeMock = vi.fn((): void => {
    /** no op */
  })

  beforeEach(() => {
    // Reset all stubs
    inHoverRangeMock.mockReset()
    onDayClickMock.mockReset()
    onDayHoverMock.mockReset()
    onMonthNavigateMock.mockReset()
    setFirstMonthMock.mockReset()
    setSecondMonthMock.mockReset()
    resetDateRangeMock.mockReset()
  })

  it('should render the start and end dates', () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      dateRange,
      startDate,
      endDate,
      inHoverRangeMock,
      onDayClickMock,
      onDayHoverMock,
      onMonthNavigateMock,
      firstMonth,
      setFirstMonthMock,
      secondMonth,
      setSecondMonthMock,
      resetDateRangeMock
    )
    const startDateLabel = getByTestId('menu-start-date')
    const endDateLabel = getByTestId('menu-end-date')

    expect(startDateLabel).toBeDefined()
    expect(startDateLabel).toHaveTextContent(format(startDate, 'MMMM dd, yyyy'))

    expect(endDateLabel).toBeDefined()
    expect(endDateLabel).toHaveTextContent(format(endDate, 'MMMM dd, yyyy'))

    expect(onDayClickMock).toBeCalledTimes(0)
    expect(onDayHoverMock).toBeCalledTimes(0)
    expect(onMonthNavigateMock).toBeCalledTimes(0)
    expect(setFirstMonthMock).toBeCalledTimes(0)
    expect(setSecondMonthMock).toBeCalledTimes(0)
  })

  it('should render the start and end dates defaults when no range is specified', () => {
    const { getByTestId } = setup(
      {},
      startDate,
      endDate,
      inHoverRangeMock,
      onDayClickMock,
      onDayHoverMock,
      onMonthNavigateMock,
      firstMonth,
      setFirstMonthMock,
      secondMonth,
      setSecondMonthMock,
      resetDateRangeMock
    )
    const startDateLabel = getByTestId('menu-start-date')
    const endDateLabel = getByTestId('menu-end-date')

    expect(startDateLabel).toBeDefined()
    expect(startDateLabel).toHaveTextContent('Start Date')

    expect(endDateLabel).toBeDefined()
    expect(endDateLabel).toHaveTextContent('End Date')
  })
})
