import { ThemeProvider } from '@mui/material/styles'
import { render } from '@testing-library/react'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { theme } from 'app/theme'
import React from 'react'

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
})
