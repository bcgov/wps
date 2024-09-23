import { render } from '@testing-library/react'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import ValidatedForecastCell from '@/features/moreCast2/components/ValidatedForecastCell'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { Provider } from 'react-redux'
import { buildTestStore } from '@/features/moreCast2/components/testHelper.test'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
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
