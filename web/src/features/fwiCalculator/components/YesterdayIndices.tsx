import { TableCell, TableRow } from '@material-ui/core'
import { YesterdayIndices } from 'api/fwiAPI'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface YesterdayIndexCellsProps {
  isLoading: boolean
  yesterdayActuals?: YesterdayIndices
}

const YesterdayIndexCells = ({ yesterdayActuals }: YesterdayIndexCellsProps) => {
  return (
    <React.Fragment>
      <TableRow>
        <TableCell>Yesterday&apos;s FFMC</TableCell>
        <TableCell>{yesterdayActuals?.ffmc?.toFixed(DECIMAL_PLACES)}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DMC</TableCell>
        <TableCell>{yesterdayActuals?.dmc?.toFixed(DECIMAL_PLACES)}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DC</TableCell>
        <TableCell>{yesterdayActuals?.dc?.toFixed(DECIMAL_PLACES)}</TableCell>
      </TableRow>
    </React.Fragment>
  )
}
export default React.memo(YesterdayIndexCells)
