import { Table } from '@devexpress/dx-react-grid-material-ui'
import { TextField } from '@material-ui/core'
import { inputColumns } from 'features/fwiCalculator/components/dataModel'
import React from 'react'

// eslint-disable-next-line
export const MultiFWITableCell = (props: any): JSX.Element => {
  const { column } = props
  const isNumericCell = inputColumns.includes(column.name)

  return isNumericCell ? (
    <Table.Cell {...props}>
      <TextField inputMode="numeric" size="small" value={props.value} />
    </Table.Cell>
  ) : (
    <Table.Cell {...props}>{props.value}</Table.Cell>
  )
}
