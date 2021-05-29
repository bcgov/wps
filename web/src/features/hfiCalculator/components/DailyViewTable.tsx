import React from 'react'

import { Paper, Table, TableBody, TableContainer, TableHead, TableRow, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

interface Props {
    title: string
    testId?: string
}

const DailyViewTable = (props: Props) => {
    const useStyles = makeStyles({
        display: {
            paddingBottom: 12,
        
            '& .MuiTableCell-sizeSmall': {
              padding: '6px 12px 6px 6px'
            }
          },
          paper: {
            width: '100%'
          },
          tableContainer: {
            maxHeight: 280
          },
    })

    const classes = useStyles()
  return (
    <div className={classes.display} data-testid={props.testId}>
        <Typography component="div" variant="subtitle2">
            {props.title}
        </Typography>
        <Paper className={classes.paper} elevation={1}>
            <TableContainer className={classes.tableContainer}>
                <Table stickyHeader size="small" aria-label="daily table view of HFI by planning area">
                    <TableHead>
                        <TableRow>

                        </TableRow>
                    </TableHead>
                    <TableBody>
                        
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    </div>
  )
}

export default React.memo(DailyViewTable)