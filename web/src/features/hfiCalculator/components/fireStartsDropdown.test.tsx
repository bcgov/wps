import { render, fireEvent, within, waitFor } from '@testing-library/react'
import FireStartsDropdown from 'features/hfiCalculator/components/FireStartsDropdown'
import {
  highestFireStarts,
  lowestFireStarts
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'
describe('FireStartsDropdown', () => {
  const testAreaId = 1
  const dayOffset = 0
  it('should render with the default value', async () => {
    const setFireStartsMock = jest.fn()
    const { getByTestId } = render(
      <FireStartsDropdown
        fireStarts={lowestFireStarts}
        areaId={testAreaId}
        dayOffset={dayOffset}
        setFireStarts={setFireStartsMock}
      />
    )
    const autocomplete = getByTestId('fire-starts-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    await waitFor(() => expect(input.value).toBe(lowestFireStarts.label))
    await waitFor(() => expect(setFireStartsMock).toBeCalledTimes(0))
  })
  it('should change value on change and call parent callback', async () => {
    const setFireStartsMock = jest.fn()
    const { getByTestId } = render(
      <FireStartsDropdown
        fireStarts={lowestFireStarts}
        areaId={testAreaId}
        dayOffset={dayOffset}
        setFireStarts={setFireStartsMock}
      />
    )
    const autocomplete = getByTestId('fire-starts-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    autocomplete.focus()
    // assign value to input field
    fireEvent.change(input, { target: { value: '6+' } })
    fireEvent.keyDown(autocomplete, { key: 'ArrowDown' })
    fireEvent.keyDown(autocomplete, { key: 'Enter' })

    await waitFor(() => expect(input.value).toBe('6+'))
    await waitFor(() => expect(setFireStartsMock).toBeCalledTimes(1))
    await waitFor(() =>
      expect(setFireStartsMock).toBeCalledWith(testAreaId, dayOffset, highestFireStarts)
    )
  })
})
