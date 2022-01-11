import { Table } from '@devexpress/dx-react-grid-material-ui'
import { TextField } from '@material-ui/core'
import { inputColumns } from 'features/fwiCalculator/components/dataModel'
import { MultiFWIStaticCell } from 'features/fwiCalculator/components/MultiFWIStaticCell'
import React from 'react'

// eslint-disable-next-line
export const MultiFWITableCell = (props: any): JSX.Element => {
  const { column } = props
  const isNumericCell = inputColumns.includes(column.name)

  return isNumericCell ? (
    <Table.Cell {...props}>
      <TextField
        inputMode="numeric"
        size="small"
        inputProps={{ style: { fontSize: '0.875rem' } }}
        value={props.value}
      />
    </Table.Cell>
  ) : (
    <MultiFWIStaticCell {...props}></MultiFWIStaticCell>
  )
}
