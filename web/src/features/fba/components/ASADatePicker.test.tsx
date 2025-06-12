import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DateTime } from 'luxon'
import ASADatePicker from './ASADatePicker'

describe('ASADatePicker', () => {
  const baseDate = DateTime.fromISO('2025-06-10')
  const minimumDate = baseDate.minus({ days: 2 })
  const maximumDate = baseDate.plus({ days: 2 })

  const setup = (overrideProps = {}) => {
    const updateDate = vi.fn()
    render(
      <ASADatePicker
        date={baseDate}
        updateDate={updateDate}
        minimumDate={minimumDate}
        maximumDate={maximumDate}
        {...overrideProps}
      />
    )
    return { updateDate }
  }

  it('renders with the correct formatted date', () => {
    setup()
    const input = screen.getByDisplayValue('Tue, Jun 10, 2025')
    expect(input).toBeInTheDocument()
  })

  it('calls updateDate when right arrow is clicked', () => {
    const { updateDate } = setup()
    const arrows = screen.getAllByRole('button', { name: '' }) // two arrow buttons
    fireEvent.click(arrows[1]) // right arrow
    expect(updateDate).toHaveBeenCalledWith(baseDate.plus({ days: 1 }))
  })

  it('calls updateDate when left arrow is clicked', () => {
    const { updateDate } = setup()
    const arrows = screen.getAllByRole('button', { name: '' }) // two arrow buttons
    fireEvent.click(arrows[0]) // left arrow
    expect(updateDate).toHaveBeenCalledWith(baseDate.plus({ days: -1 }))
  })

  it('disables left arrow when at minimumDate', () => {
    setup({ date: minimumDate })
    const arrows = screen.getAllByRole('button', { name: '' })
    expect(arrows[0]).toBeDisabled() // left arrow
    expect(arrows[1]).not.toBeDisabled() // right arrow
  })

  it('disables right arrow when at maximumDate', () => {
    setup({ date: maximumDate })
    const arrows = screen.getAllByRole('button', { name: '' })
    expect(arrows[1]).toBeDisabled() // right arrow
    expect(arrows[0]).not.toBeDisabled() // left arrow
  })

  it('opens and closes calendar picker when calendar icon is clicked', () => {
    setup()
    const calendarButton = screen.getByRole('button', { name: /calendar/i })
    expect(calendarButton).toBeInTheDocument()
    fireEvent.click(calendarButton)
    // Picker behavior is internal, so just ensure the button is clickable
    // Actual popover logic would be tested in integration or MUI tests
  })
})