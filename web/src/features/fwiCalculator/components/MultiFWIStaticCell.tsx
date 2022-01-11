import { Table } from '@devexpress/dx-react-grid-material-ui'
import React from 'react'

// eslint-disable-next-line
export const MultiFWIStaticCell = (props: any): JSX.Element => {
  const { column, style, value } = props
  const isAdjustedStatus =
    column.name === 'status' && String(value).toLowerCase() === 'adjusted'

  return isAdjustedStatus ? (
    <Table.Cell
      {...props}
      style={{
        ...style,
        color: 'purple',
        fontWeight: 'bold'
      }}
    >
      {props.value}
    </Table.Cell>
  ) : (
    <Table.Cell {...props}>{props.value}</Table.Cell>
  )
}
