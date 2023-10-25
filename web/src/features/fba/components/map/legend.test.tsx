import Legend from 'features/fba/components/map/Legend'
import { render, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'

describe('Legend', () => {
  it('should render with the default layer visibility', async () => {
    const onToggleLayer = jest.fn()
    const setShowZoneStatus = jest.fn()
    const setShowHFI = jest.fn()
    const { getByTestId } = render(
      <Legend
        onToggleLayer={onToggleLayer}
        setShowShapeStatus={setShowZoneStatus}
        setShowHFI={setShowHFI}
        showHFI={false}
        showZoneStatus={true}
      />
    )
    const legendComponent = getByTestId('asa-map-legend')
    await waitFor(() => expect(legendComponent).toBeInTheDocument())

    const zoneStatus = getByTestId('zone-checkbox')
    const zoneStatusCheckbox = within(zoneStatus).getByRole('checkbox')
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked())
    await waitFor(() => expect(setShowZoneStatus).not.toHaveBeenCalled())

    const hfi = getByTestId('hfi-checkbox')
    const hfiCheckbox = within(hfi).getByRole('checkbox')
    await waitFor(() => expect(hfiCheckbox).not.toBeChecked())
    await waitFor(() => expect(setShowHFI).not.toHaveBeenCalled())
  })

  it('should call click handlers on checkboxes', async () => {
    const onToggleLayer = jest.fn()
    const setShowZoneStatus = jest.fn()
    const setShowHFI = jest.fn()
    const { getByTestId } = render(
      <Legend
        onToggleLayer={onToggleLayer}
        setShowShapeStatus={setShowZoneStatus}
        setShowHFI={setShowHFI}
        showHFI={false}
        showZoneStatus={true}
      />
    )

    const zoneStatus = getByTestId('zone-checkbox')
    const zoneStatusCheckbox = within(zoneStatus).getByRole('checkbox')
    await userEvent.click(zoneStatusCheckbox)
    await waitFor(() => expect(setShowZoneStatus).toBeCalledTimes(1))

    const hfi = getByTestId('hfi-checkbox')
    const hfiCheckbox = within(hfi).getByRole('checkbox')
    await userEvent.click(hfiCheckbox)
    await waitFor(() => expect(setShowHFI).toBeCalledTimes(1))
  })
})
