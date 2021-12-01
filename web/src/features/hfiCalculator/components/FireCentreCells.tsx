import { makeStyles, TableCell } from '@material-ui/core'
import { FireCentre } from 'api/hfiCalcAPI'
import { fireTableStyles } from 'app/theme'
import StickyCell from 'components/StickyCell'
import React from 'react'

interface FireCentreCellsProps {
  centre: FireCentre
  testId?: string
}

const useStyles = makeStyles({ ...fireTableStyles })

const FireCentreCells = (props: FireCentreCellsProps) => {
  const classes = useStyles()

  return (
    <StickyCell
      left={0}
      zIndexOffset={10}
      backgroundColor={'#dbd9d9'}
      colSpan={4}
      data-testid={props.testId}
    >
      <TableCell className={`${classes.fireCentre} ${classes.noBottomBorder}`}>
        {props.centre.name}
      </TableCell>
    </StickyCell>
  )
}

export default React.memo(FireCentreCells)
