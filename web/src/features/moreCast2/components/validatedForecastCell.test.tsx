import { prettyDOM, render, within } from '@testing-library/react'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import ValidatedForecastCell from '@/features/moreCast2/components/ValidatedForecastCell'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import morecastInputValidSlice, { initialState, ValidInputState } from '@/features/moreCast2/slices/validInputSlice'
import { Provider } from 'react-redux'
import { theme } from '@/app/theme'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
}

const buildTestStore = (initialState: ValidInputState) => {
  const rootReducer = combineReducers({
    morecastInputValid: morecastInputValidSlice
  })
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      morecastInputValid: initialState
    }
  })
  return testStore
}

describe('ValidatedForecastCell', () => {
  it('should render a tooltip when value is invalid', async () => {
    const testStore = buildTestStore(initialState)

    const { queryByText } = render(
      <Provider store={testStore}>
        <ValidatedForecastCell
          disabled={false}
          label="foo"
          value={params.formattedValue}
          validator={() => 'tooltip-error'}
        />
      </Provider>
    )
    expect(queryByText('tooltip-error')).toBeInTheDocument()
  })

  it('should not render a tooltip when value is valid', async () => {
    const testStore = buildTestStore(initialState)
    const { queryByText } = render(
      <Provider store={testStore}>
        <ValidatedForecastCell
          disabled={false}
          label="foo"
          value={params.formattedValue}
          validator={v => (Number(v) > Number.MAX_VALUE ? 'tooltip-error' : '')}
        />
      </Provider>
    )

    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })
})
