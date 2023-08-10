import { fireEvent, render, waitFor, within } from '@testing-library/react'
import { MARKERS } from 'components/dateRangePicker/DateRangePicker'
import Month from 'components/dateRangePicker/Month'
import { DateRange, NavigationAction } from 'components/dateRangePicker/types'
import React from 'react'
/* eslint-disable @typescript-eslint/no-unused-vars */

const setup = (
  value: Date,
  setValueStub: (date: Date) => void,
  dateRange: DateRange,
  minDate: Date,
  maxDate: Date,
  inHoverRangeMock: (date: Date) => boolean,
  onDayClickMock: (date: Date) => void,
  onDayHoverMock: (date: Date) => void,
  onMonthNavigateMock: (marker: symbol, action: NavigationAction) => void
) => {
  const { getByTestId, getByRole } = render(
    <Month
      testId="testMonth"
      value={value}
      marker={MARKERS.FIRST_MONTH}
      dateRange={dateRange}
      minDate={minDate}
      maxDate={maxDate}
      navState={[true, true]}
      setValue={setValueStub}
      helpers={{
        inHoverRange: inHoverRangeMock
      }}
      handlers={{
        onDayClick: onDayClickMock,
        onDayHover: onDayHoverMock,
        onMonthNavigate: onMonthNavigateMock
      }}
    />
  )
  return { getByTestId, getByRole }
}
describe('Month', () => {
  const startDate = new Date('2021/2/21')
  const endDate = new Date('2021/2/25')
  const setValueMock = jest.fn((date: Date): void => {
    /** no op */
  })
  const inHoverRangeMock = jest.fn((date: Date): boolean => {
    return false
  })
  const onDayClickMock = jest.fn((date: Date): void => {
    /** no op */
  })
  const onDayHoverMock = jest.fn((date: Date): void => {
    /** no op */
  })
  const onMonthNavigateMock = jest.fn((marker: symbol, action: NavigationAction): void => {
    /** no op */
  })

  beforeEach(() => {
    // Reset all stubs
    setValueMock.mockReset()
    inHoverRangeMock.mockReset()
    onDayClickMock.mockReset()
    onDayHoverMock.mockReset()
    onMonthNavigateMock.mockReset()
  })

  it('should render the month', () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      startDate,
      setValueMock,
      dateRange,
      startDate,
      endDate,
      inHoverRangeMock,
      onDayClickMock,
      onDayHoverMock,
      onMonthNavigateMock
    )
    const month = getByTestId('testMonth')

    expect(month).toBeDefined()
    expect(setValueMock).toBeCalledTimes(0)
    expect(onDayClickMock).toBeCalledTimes(0)
    expect(onDayHoverMock).toBeCalledTimes(0)
    expect(onMonthNavigateMock).toBeCalledTimes(0)
  })
  it('should handle day clicks', async () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      startDate,
      setValueMock,
      dateRange,
      startDate,
      endDate,
      inHoverRangeMock,
      onDayClickMock,
      onDayHoverMock,
      onMonthNavigateMock
    )
    const startDay = getByTestId(`day-${startDate.toISOString().split('T')[0]}`)

    expect(startDay.className).toMatch(/Day-buttonContainer/)
    const startDayButton = within(startDay).getByRole('button') as HTMLInputElement

    startDayButton.focus()
    fireEvent.click(startDayButton)
    await waitFor(() => expect(onDayClickMock).toBeCalledTimes(1))

    const endDay = getByTestId(`day-${endDate.toISOString().split('T')[0]}`)

    const endDayButton = within(endDay).getByRole('button') as HTMLInputElement
    endDayButton.focus()

    fireEvent.click(endDayButton)
    await waitFor(() => expect(onDayClickMock).toBeCalledTimes(2))

    expect(onDayHoverMock).toBeCalledTimes(0)
    expect(onMonthNavigateMock).toBeCalledTimes(0)
  })
  it('should disable day buttons outside of 7 day range', async () => {
    const dateRange = { startDate: new Date('2021/2/1'), endDate: new Date('2021/2/7') }
    const dateOutOfRange = new Date('2021/2/8')
    const { getByTestId } = setup(
      startDate,
      setValueMock,
      dateRange,
      dateRange.startDate,
      dateRange.endDate,
      inHoverRangeMock,
      onDayClickMock,
      onDayHoverMock,
      onMonthNavigateMock
    )
    const dayOutOfRange = getByTestId(`day-${dateOutOfRange.toISOString().split('T')[0]}`)
    const outOfRangeButton = within(dayOutOfRange).getByRole('button') as HTMLInputElement

    expect(outOfRangeButton).toBeDisabled()
    expect(outOfRangeButton.className).toMatch(/Mui-disabled/)
  })
})
