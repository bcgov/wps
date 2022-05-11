import { Table } from '@devexpress/dx-react-grid-material-ui'
import makeStyles from '@mui/styles/makeStyles'
import { inputColumns } from 'features/fwiCalculator/components/dataModel'
import React from 'react'

const useStyles = makeStyles({
  adjusted: {
    color: 'purple',
    fontWeight: 'bold'
  },
  input: {
    textDecoration: 'underline'
  }
})

// eslint-disable-next-line
export const MultiFWITableCell = (props: any): JSX.Element => {
  const classes = useStyles()

  const { onClick, ...restProps } = props
  const isNumericEditableCell = inputColumns.includes(restProps.column.name)

  if (isNumericEditableCell) {
    return <Table.Cell className={classes.input} {...restProps} tabIndex={0} onFocus={onClick} />
  }

  const isAdjustedStatus = restProps.column.name === 'status' && String(restProps.value).toLowerCase() === 'adjusted'
  const classToApply = isAdjustedStatus ? classes.adjusted : undefined
  return <Table.Cell className={classToApply} {...restProps} />
}
