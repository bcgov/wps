import { makeStyles, Table, TableBody, TableCell, TableRow } from '@material-ui/core'
import { fireTableStyles } from 'app/theme'
import StickyCell from 'components/StickyCell'
import React, { ReactElement } from 'react'

const useStyles = makeStyles({
  ...fireTableStyles
})

export const StationDataHeaderCells = (): ReactElement => {
  const classes = useStyles()

  return (
    <React.Fragment>
      <StickyCell left={50} zIndexOffset={12}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell
                key="header-location"
                className={`${classes.noBottomBorder} ${classes.tableColumnHeader}`}
              >
                Location
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <TableCell key="header-elevation" className={classes.nonstickyHeaderCell}>
        Elev.
        <br />
        (m)
      </TableCell>
      <StickyCell left={230} zIndexOffset={12}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell
                key="header-fuel-type"
                className={`${classes.noBottomBorder} ${classes.tableColumnHeader}`}
              >
                FBP
                <br />
                Fuel
                <br />
                Type
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <StickyCell left={275} zIndexOffset={12} className={classes.rightBorder}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell
                className={`${classes.noBottomBorder} ${classes.tableColumnHeader}`}
              >
                Grass
                <br />
                Cure
                <br />
                (%)
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
    </React.Fragment>
  )
}

export default React.memo(StationDataHeaderCells)
