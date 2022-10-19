import { TableCell, TableRow, Skeleton } from '@mui/material'
import { YesterdayIndices } from 'api/fwiAPI'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface YesterdayIndexCellsProps {
  isLoading: boolean
  yesterdayActuals?: YesterdayIndices
}

const YesterdayIndexCells = ({ yesterdayActuals, isLoading }: YesterdayIndexCellsProps) => {
  return (
    <React.Fragment>
      <TableRow>
        <TableCell>Yesterday&apos;s FFMC</TableCell>
        {isLoading ? (
          <TableCell>
            <Skeleton />
          </TableCell>
        ) : (
          <TableCell align="right">{yesterdayActuals?.ffmc?.toFixed(DECIMAL_PLACES)}</TableCell>
        )}
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DMC</TableCell>
        {isLoading ? (
          <TableCell>
            <Skeleton />
          </TableCell>
        ) : (
          <TableCell align="right">{yesterdayActuals?.dmc?.toFixed(DECIMAL_PLACES)}</TableCell>
        )}
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DC</TableCell>
        {isLoading ? (
          <TableCell>
            <Skeleton />
          </TableCell>
        ) : (
          <TableCell align="right">{yesterdayActuals?.dc?.toFixed(DECIMAL_PLACES)}</TableCell>
        )}
      </TableRow>
    </React.Fragment>
  )
}
export default React.memo(YesterdayIndexCells)
