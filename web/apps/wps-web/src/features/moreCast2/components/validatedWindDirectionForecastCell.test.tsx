import type { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { render } from '@testing-library/react'
import { Provider } from 'react-redux'
import { buildTestStore } from '@/features/moreCast2/components/testHelper'
import ValidatedWindDirectionForecastCell from '@/features/moreCast2/components/ValidatedWindDirectionForecastCell'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
}

describe('ValidatedWindDirectionForecastCell', () => {
  it('should render a tooltip when value is invalid', async () => {
    const testStore = buildTestStore(initialState)

    const { queryByText } = render(
      <Provider store={testStore}>
        <ValidatedWindDirectionForecastCell
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
        <ValidatedWindDirectionForecastCell
          disabled={false}
          label="foo"
          value={params.formattedValue}
          validator={() => ''}
        />
      </Provider>
    )

    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })

  it('should not render a tooltip when value has no validator', async () => {
    const testStore = buildTestStore(initialState)
    const { queryByText } = render(
      <Provider store={testStore}>
        <ValidatedWindDirectionForecastCell disabled={false} label="foo" value={params.formattedValue} />
      </Provider>
    )

    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })
})
