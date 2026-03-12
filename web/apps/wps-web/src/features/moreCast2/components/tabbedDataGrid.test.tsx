import { vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { Provider } from 'react-redux'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { DateRange } from 'components/dateRangePicker/types'
import store from 'app/store'

const FROM_TO: DateRange = {}
const SET_FROM_TO: React.Dispatch<React.SetStateAction<DateRange>> = vi.fn()
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

describe('TabbedDataGrid', () => {
  const fetchWeatherIndeterminatesMock = vi.fn((): void => {})
  test('Only temp tab is selected on load', async () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <TabbedDataGrid
          fromTo={FROM_TO}
          setFromTo={SET_FROM_TO}
          fetchWeatherIndeterminates={fetchWeatherIndeterminatesMock}
        />
      </Provider>
    )

    for (const tab of TABS) {
      if (tab === TABS[0]) {
        const tabElement = getByTestId(`${tab}-selected`)
        await waitFor(() => expect(tabElement).toBeInTheDocument())
      } else {
        const tabElement = getByTestId(`${tab}-unselected`)
        expect(tabElement).toBeVisible()
      }
    }
  })

  test('Forecast column visibility', async () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={store}>
        <TabbedDataGrid
          fromTo={FROM_TO}
          setFromTo={SET_FROM_TO}
          fetchWeatherIndeterminates={fetchWeatherIndeterminatesMock}
        />
      </Provider>
    )
    // // Temp forecast column is visible on load
    await waitFor(() => expect(getByTestId('tempForecast-column-header')).toBeDefined())
    const selectedTabButton = getByTestId(`${TABS[0]}-selected`)
    // // Toggle off Temp tab which should hide temp forecast column
    await userEvent.click(selectedTabButton)
    await waitFor(() => expect(queryByTestId('tempForecast-column-header')).not.toBeInTheDocument())
    // // Toggle on Temp tab and ensure temp forecast column is visible again
    const unselectedTabButton = getByTestId(`${TABS[0]}-unselected`)
    await userEvent.click(unselectedTabButton)
    await waitFor(() => expect(getByTestId('tempForecast-column-header')).toBeDefined())
  })

  test('AboutDataPopover is rendered and opens on click', async () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={store}>
        <TabbedDataGrid
          fromTo={FROM_TO}
          setFromTo={SET_FROM_TO}
          fetchWeatherIndeterminates={fetchWeatherIndeterminatesMock}
        />
      </Provider>
    )

    // popover trigger should be in the document
    const aboutDataTrigger = getByTestId('about-data-trigger')
    expect(aboutDataTrigger).toBeInTheDocument()

    // content shouldn't be visible initially
    expect(queryByTestId('morecast-about-data-content')).not.toBeInTheDocument()

    await userEvent.click(aboutDataTrigger)

    // content should be visible after click
    expect(getByTestId('morecast-about-data-content')).toBeInTheDocument()
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
