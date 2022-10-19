import { Table, TableBody, TableRow, TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FireCentre } from 'api/hfiCalculatorAPI'
import { fireTableStyles } from 'app/theme'
import StickyCell from 'components/StickyCell'
import React from 'react'

interface FireCentreCellProps {
  centre: FireCentre
  testId?: string
}

const useStyles = makeStyles({ ...fireTableStyles })

const FireCentreCell = (props: FireCentreCellProps) => {
  const classes = useStyles()

  return (
    <StickyCell left={0} zIndexOffset={10} backgroundColor={'#dbd9d9'} colSpan={4} data-testid={props.testId}>
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className={`${classes.fireCentre} ${classes.noBottomBorder}`}>{props.centre.name}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </StickyCell>
  )
}

export default React.memo(FireCentreCell)
