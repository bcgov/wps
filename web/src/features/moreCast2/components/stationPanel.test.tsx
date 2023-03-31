import { ThemeProvider } from '@mui/material/styles'
import { render, waitFor, within } from '@testing-library/react'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { theme } from 'app/theme'
import React from 'react'
import userEvent from '@testing-library/user-event'

describe('StationPanel', () => {
  it('should render the panel', () => {
    const mockSetSelectedStationGroup = jest.fn()
    const mockSetSelectedStations = jest.fn()

    const { getByTestId } = render(
      <ThemeProvider theme={theme}>
        <StationPanel
          loading={false}
          stationGroups={[]}
          selectedStations={[]}
          stationGroupMembers={[]}
          setSelectedStationGroup={mockSetSelectedStationGroup}
          setSelectedStations={mockSetSelectedStations}
        />
      </ThemeProvider>
    )
    const panel = getByTestId('morecast2-station-panel')
    expect(panel).toBeDefined()
  })

  it('should allow selecting of stations', async () => {
    const mockSetSelectedStationGroup = jest.fn()
    const mockSetSelectedStations = jest.fn()

    const { getByTestId } = render(
      <ThemeProvider theme={theme}>
        <StationPanel
          loading={false}
          stationGroups={[]}
          selectedStations={[]}
          stationGroupMembers={[
            {
              id: '1',
              station_code: 1,
              station_status: 1,
              display_label: '1',
              fire_centre: { id: '1', display_label: '1' },
              fire_zone: { id: '1', display_label: '1', fire_centre: '1' }
            }
          ]}
          setSelectedStationGroup={mockSetSelectedStationGroup}
          setSelectedStations={mockSetSelectedStations}
        />
      </ThemeProvider>
    )
    const stationList = getByTestId('station-items')
    expect(stationList).toBeDefined()
    const item = within(stationList).getByRole('listitem')
    const checkboxButton = within(item).getByRole('button') as HTMLInputElement

    await userEvent.click(checkboxButton)

    await waitFor(() => expect(mockSetSelectedStations).toBeCalledTimes(1))
  })
})
