import { render } from '@testing-library/react'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { Provider } from 'react-redux'
import ValidatedGrassCureForecastCell from '@/features/moreCast2/components/ValidatedGrassCureForecastCell'
import { buildTestStore } from '@/features/moreCast2/components/testHelper'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
}

describe('ValidatedGrassCureForecastCell', () => {
  it('should render a tooltip when value is invalid', async () => {
    const testStore = buildTestStore(initialState)

    const { queryByText } = render(
      <Provider store={testStore}>
        <ValidatedGrassCureForecastCell
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
        <ValidatedGrassCureForecastCell
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
        <ValidatedGrassCureForecastCell disabled={false} label="foo" value={params.formattedValue} />
      </Provider>
    )

    expect(queryByText('tooltip-error')).not.toBeInTheDocument()
  })
})
