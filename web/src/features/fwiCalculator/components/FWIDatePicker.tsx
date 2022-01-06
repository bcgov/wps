import React from 'react'
import { Grid, FormControl } from '@material-ui/core'
import DatePicker from 'components/DatePicker'

export interface FWIDateRangeProps {
  isBasic: boolean
  startDate: string
  endDate: string
  updateStartDate: (newDate: string) => void
  updateEndDate: (newDate: string) => void
  dateClassName: string
}

const FWIDateRange = ({
  isBasic,
  startDate,
  updateStartDate,
  updateEndDate,
  endDate,
  dateClassName
}: FWIDateRangeProps) => {
  return (
    <React.Fragment>
      <Grid item xs={isBasic ? 5 : 4}>
        <FormControl className={dateClassName}>
          <DatePicker
            label={isBasic ? 'Date of Interest (PST-08:00)' : 'Start Date'}
            date={startDate}
            updateDate={updateStartDate}
          />
        </FormControl>
      </Grid>
      {!isBasic && (
        <Grid item xs={4}>
          <FormControl className={dateClassName}>
            <DatePicker label={'End Date'} date={endDate} updateDate={updateEndDate} />
          </FormControl>
        </Grid>
      )}
    </React.Fragment>
  )
}
export default React.memo(FWIDateRange)
