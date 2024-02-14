import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { DateRange } from 'components/dateRangePicker/types'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import store from 'app/store'
import { createTheme } from '@mui/material/styles'

const EMPTY_MORECAST_2_ROWS: MoreCast2Row[] = []
const FROM_TO: DateRange = {}
const SET_FROM_TO: React.Dispatch<React.SetStateAction<DateRange>> = jest.fn()
const TABS = [
  'temp-tab-button',
  'rh-tab-button',
  'wind-direction-tab-button',
  'wind-speed-tab-button',
  'precip-tab-button',
  'summary-tab-button'
]
// Leaving this here for future tests
// const TEMPERATURE_WEATHER_MODELS_HEADERS = [
//   'tempHRDPS-column-header',
//   'tempHRDPS_BIAS-column-header',
//   'tempRDPS-column-header',
//   'tempRDPS_BIAS-column-header',
//   'tempGDPS-column-header',
//   'tempGDPS_BIAS-column-header',
//   'tempNAM-column-header',
//   'tempNAM_BIAS-column-header',
//   'tempGFS-column-header',
//   'tempGFS_BIAS-column-header'
// ]
const theme = createTheme()

const hexToRgb = (hex: string): string => {
  if (hex.startsWith('#')) {
    hex = hex.slice(1)
  }
  const value = parseInt(hex, 16)
  const red = (value >> 16) & 0xff
  const green = (value >> 8) & 0xff
  const blue = value & 0xff
  return `rgb(${red}, ${green}, ${blue})`
}

const convertRgbaToRgb = (rgba: string): string => {
  if (rgba.startsWith(rgba)) {
    const temp = rgba.slice(5)
    const split = temp.split(',').map(item => item.trim())
    return `rgb(${split[0]}, ${split[1]}, ${split[2]})`
  }
  return ''
}

describe('TabbedDataGrid', () => {
  test('Only temp tab is selected on load', () => {
    render(
      <Provider store={store}>
        <TabbedDataGrid morecast2Rows={EMPTY_MORECAST_2_ROWS} fromTo={FROM_TO} setFromTo={SET_FROM_TO} />
      </Provider>
    )
    const tab = screen.getByTestId('temp-tab-button')
    expect(tab).toBeVisible()
    const style = getComputedStyle(tab)
    // A dark background color indicates the tab is selected
    expect(style.backgroundColor).toBe(hexToRgb(theme.palette.primary.dark))

    for (const tab of TABS) {
      const tabElement = screen.getByTestId(tab)
      expect(tabElement).toBeVisible()
      const style = getComputedStyle(tabElement)
      if (tab === TABS[0]) {
        expect(style.backgroundColor).toBe(hexToRgb(theme.palette.primary.dark))
      } else {
        const bgColor = convertRgbaToRgb(style.backgroundColor)
        expect(bgColor).toBe(hexToRgb(theme.palette.primary.main))
      }
    }
  })

  test('Forecast column visibility', async () => {
    render(
      <Provider store={store}>
        <TabbedDataGrid morecast2Rows={EMPTY_MORECAST_2_ROWS} fromTo={FROM_TO} setFromTo={SET_FROM_TO} />
      </Provider>
    )
    // Temp forecast column is visible on load
    await waitFor(() => expect(screen.getByTestId('tempForecast-column-header')).toBeDefined())
    const tempTabElement = screen.getByTestId(TABS[0])
    // Toggle off Temp tab which should hide temp forecast column
    fireEvent.click(tempTabElement)
    await waitFor(() => expect(screen.queryByTestId('tempForecast-column-header')).not.toBeInTheDocument())
    // Toggle on Temp tab and ensure temp forecast column is visible again
    fireEvent.click(tempTabElement)
    await waitFor(() => expect(screen.getByTestId('tempForecast-column-header')).toBeDefined())
  })
})

// Leaving this here for future tests
// const moreCast2Row: MoreCast2Row = {
//   id: 'testId',
//   stationCode: 123,
//   stationName: 'foo',
//   forDate: DateTime.now(),
//   latitude: 49,
//   longitude: -121,
//   ffmcCalcActual: 1,
//   dmcCalcActual: 1,
//   dcCalcActual: 1,
//   isiCalcActual: 1,
//   buiCalcActual: 1,
//   fwiCalcActual: 1,
//   dgrCalcActual: 1,
//   grassCuringActual: 1,
//   precipActual: 0,
//   rhActual: 95,
//   tempActual: 3,
//   windDirectionActual: 121,
//   windSpeedActual: 6.5,
//   precipGDPS: 0,
//   rhGDPS: 0,
//   tempGDPS: 0,
//   windDirectionGDPS: 0,
//   windSpeedGDPS: 0,
//   precipGDPS_BIAS: 0,
//   rhGDPS_BIAS: 0,
//   tempGDPS_BIAS: 0,
//   windDirectionGDPS_BIAS: 0,
//   windSpeedGDPS_BIAS: 0,
//   precipGFS: 0,
//   rhGFS: 0,
//   tempGFS: 0,
//   windDirectionGFS: 0,
//   windSpeedGFS: 0,
//   precipGFS_BIAS: 0,
//   rhGFS_BIAS: 0,
//   tempGFS_BIAS: 0,
//   windDirectionGFS_BIAS: 0,
//   windSpeedGFS_BIAS: 0,
//   precipHRDPS: 0,
//   rhHRDPS: 0,
//   tempHRDPS: 0,
//   windDirectionHRDPS: 0,
//   windSpeedHRDPS: 0,
//   precipHRDPS_BIAS: 0,
//   rhHRDPS_BIAS: 0,
//   tempHRDPS_BIAS: 0,
//   windDirectionHRDPS_BIAS: 0,
//   windSpeedHRDPS_BIAS: 0,
//   precipNAM: 0,
//   rhNAM: 0,
//   tempNAM: 0,
//   windDirectionNAM: 0,
//   windSpeedNAM: 0,
//   precipNAM_BIAS: 0,
//   rhNAM_BIAS: 0,
//   tempNAM_BIAS: 0,
//   windDirectionNAM_BIAS: 0,
//   windSpeedNAM_BIAS: 0,
//   precipRDPS: 0,
//   rhRDPS: 0,
//   tempRDPS: 0,
//   windDirectionRDPS: 0,
//   windSpeedRDPS: 0,
//   precipRDPS_BIAS: 0,
//   rhRDPS_BIAS: 0,
//   tempRDPS_BIAS: 0,
//   windDirectionRDPS_BIAS: 0,
//   windSpeedRDPS_BIAS: 0
// }
