import Legend from 'features/fba/components/map/Legend'
import { render, waitFor, within } from '@testing-library/react'
import React from 'react'

describe('Legend', () => {
  it('should render with the default layer visibility', async () => {
    const onToggleLayer = jest.fn()
    const setShowZoneStatus = jest.fn()
    const setShowHFI = jest.fn()
    const { getByTestId } = render(
      <Legend
        onToggleLayer={onToggleLayer}
        setShowZoneStatus={setShowZoneStatus}
        setShowHFI={setShowHFI}
        showHFI={false}
        showZoneStatus={true}
      />
    )
    const legendComponent = getByTestId('asa-map-legend')
    await waitFor(() => expect(legendComponent).toBeInTheDocument())

    const zoneStatus = getByTestId('Zone Status-checkbox')
    const zoneStatusCheckbox = within(zoneStatus).getByRole('checkbox')
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked())

    const hfi = getByTestId('HFI Potential (kW/h)-checkbox')
    const hfiCheckbox = within(hfi).getByRole('checkbox')
    await waitFor(() => expect(hfiCheckbox).not.toBeChecked())
  })
})
