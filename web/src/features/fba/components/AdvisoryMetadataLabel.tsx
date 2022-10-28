import { Box, Grid, Typography } from '@mui/material'
import React from 'react'
import { DateTime } from 'luxon'

export interface AdvisoryMetadataLabelProps {
    testId?: string
    runType: string
    forDate: DateTime
    runDate: DateTime
}
const AdvisoryMetadataLabel = ({
    runType: run_type,
    forDate: for_date,
    runDate: run_date
}: AdvisoryMetadataLabelProps) => {
    return (
        <Box sx={{ width: 250 }}>
            <Grid container spacing={2}>
                <Grid item xs>
                    <Typography>
                        Displaying {run_type} data for {for_date.toISODate()} issued on {run_date.toISODate()}
                    </Typography>
                </Grid>
            </Grid>
        </Box>
    )
}

export default React.memo(AdvisoryMetadataLabel)
