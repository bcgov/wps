import { ColumnDefBuilder, DEFAULT_COLUMN_WIDTH } from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'
import { TempForecastField } from 'features/moreCast2/components/MoreCast2Column'

describe('ColDefBuilder', () => {
  it('should generate the col def correctly', () => {
    const colDefBuilder = new ColumnDefBuilder(
      TempForecastField.field,
      TempForecastField.headerName,
      TempForecastField.type,
      TempForecastField.precision,
      new GridComponentRenderer()
    )

    const updatedRow = colDefBuilder.generateColDef()

    expect(JSON.stringify(updatedRow)).toEqual(
      JSON.stringify({
        field: 'temp',
        disableColumnMenu: true,
        disabledReorder: true,
        headerName: 'Temp',
        sortable: false,
        type: 'number',
        width: DEFAULT_COLUMN_WIDTH
      })
    )
  })
})
