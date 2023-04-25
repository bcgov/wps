import { ColumnDefBuilder } from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'

xdescribe('ColDefBuilder', () => {
  it('should generate the col def correctly', () => {
    const colDefBuilder = new ColumnDefBuilder('temp', 'Temp', 'number', 1, new GridComponentRenderer())

    const updatedRow = colDefBuilder.generateColDef()

    expect(JSON.stringify(updatedRow)).toEqual(
      JSON.stringify({
        field: 'temp',
        disableColumnMenu: true,
        disabledReorder: true,
        headerName: 'Temp',
        sortable: false,
        type: 'number',
        width: 200
      })
    )
  })
})
