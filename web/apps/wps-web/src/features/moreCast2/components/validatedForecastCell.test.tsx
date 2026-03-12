import { render } from '@testing-library/react'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import ValidatedForecastCell from '@/features/moreCast2/components/ValidatedForecastCell'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { Provider } from 'react-redux'
import { buildTestStore } from '@/features/moreCast2/components/testHelper'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
}

describe('ValidatedForecastCell', () => {
  it('should render a tooltip and be in error state when value is invalid', async () => {
    const testStore = buildTestStore(initialState)

    const { queryByText, queryByTestId } = render(
      <Provider store={testStore}>
        <ValidatedForecastCell
          disabled={false}
          label="foo"
          value={params.formattedValue}
          validator={() => 'tooltip-error'}
        />
      </Provider>
    )
    expect(queryByTestId('validated-forecast-cell-error')).toBeInTheDocument()
    expect(queryByTestId('validated-forecast-cell')).not.toBeInTheDocument()
    expect(queryByText('tooltip-error')).toBeInTheDocument()
  })

  it('should render in an error state when value is empty and required', async () => {
    const testStore = buildTestStore({ ...initialState, isRequiredEmpty: { empty: true } })

    const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
      row: undefined,
      formattedValue: ''
    }

    const { queryByText, queryByTestId } = render(
      <Provider store={testStore}>
        <ValidatedForecastCell disabled={false} label="foo" value={params.formattedValue} />
      </Provider>
    )
    expect(queryByTestId('validated-forecast-cell-error')).toBeInTheDocument()
    expect(queryByTestId('validated-forecast-cell')).not.toBeInTheDocument()
    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })

  it('should not render a tooltip and not be in an error state when value is valid', async () => {
    const testStore = buildTestStore(initialState)
    const { queryByText, queryByTestId } = render(
      <Provider store={testStore}>
        <ValidatedForecastCell disabled={false} label="foo" value={params.formattedValue} validator={() => ''} />
      </Provider>
    )
    expect(queryByTestId('validated-forecast-cell')).toBeInTheDocument()
    expect(queryByTestId('validated-forecast-cell-error')).not.toBeInTheDocument()
    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })
})
