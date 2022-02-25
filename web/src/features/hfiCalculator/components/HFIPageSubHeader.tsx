import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import {
  Button,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  TextField
} from '@material-ui/core'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'
import { isUndefined } from 'lodash'
import { FireCentre } from 'api/hfiCalcAPI'
import AboutDataModal from 'features/hfiCalculator/components/AboutDataModal'
import { HelpOutlineOutlined } from '@material-ui/icons'
import { DateRange, DateRangePicker } from 'materialui-daterange-picker'
import * as materialIcons from '@material-ui/icons'
import { formControlStyles } from 'app/theme'
import { DateTime } from 'luxon'

const useStyles = makeStyles(theme => ({
  ...formControlStyles,
  root: {
    minHeight: 50,
    maxHeight: 62,
    marginBottom: '1rem',
    paddingBottom: '0.25rem',
    paddingTop: '0.25rem',
    paddingLeft: '1rem',
    paddingRight: '1rem',
    fontSize: '1.3rem',
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
    alignContent: 'center'
  },
  gridContainer: {
    height: '85%'
  },
  helpIcon: {
    fill: 'white'
  },
  aboutButtonText: {
    color: 'white',
    textDecoration: 'underline',
    fontWeight: 'bold',
    justifyContent: 'flex-end'
  },
  dateRangePicker: {
    zIndex: 3200
  },
  dateRangeTextField: {
    marginLeft: '8px',
    '& .MuiOutlinedInput-input': {
      color: 'white'
    },
    '& .MuiIconButton-root': {
      color: 'white'
    },
    '& .MuiInputLabel-root': {
      color: 'white'
    },
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor: 'white'
      },
      '&:hover fieldset': {
        borderColor: 'white'
      },
      '&.Mui-focused fieldset': {
        borderColor: 'white'
      }
    }
  },
  aboutButtonGridItem: {
    marginLeft: 'auto',
    minWidth: 210,
    maxHeight: 56
  },
  minWidth210: {
    minWidth: 210
  }
}))

interface Props {
  padding?: string
  fireCentres: FireCentre[]
  dateRange: DateRange | undefined
  setDateRange: (newDateRange: DateRange) => void
  selectedFireCentre: FireCentre | undefined
  selectNewFireCentre: (newSelection: FireCentre | undefined) => void
}

export const HFIPageSubHeader: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)

  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const [dateRangePickerOpen, setDateRangePickerOpen] = useState<boolean>(false)

  const dateDisplayFormat = 'MMMM dd'

  const openAboutModal = () => {
    setModalOpen(true)
  }
  const toggleDateRangePicker = () => setDateRangePickerOpen(!dateRangePickerOpen)

  return (
    <div className={classes.root}>
      <Grid
        container
        spacing={0}
        alignItems="center"
        direction="row"
        className={classes.gridContainer}
      >
        <Grid item md={3}>
          <FormControl className={classes.minWidth210}>
            <FireCentreDropdown
              fireCentres={props.fireCentres}
              selectedValue={
                isUndefined(props.selectedFireCentre)
                  ? null
                  : { name: props.selectedFireCentre?.name }
              }
              onChange={props.selectNewFireCentre}
            />
          </FormControl>
        </Grid>
        <Grid item md={3} lg={2}>
          <TextField
            className={`${classes.dateRangeTextField} ${classes.minWidth210}`}
            size="small"
            id="outlined-basic"
            variant="outlined"
            disabled={true}
            label={'Set prep period'}
            onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
            value={
              isUndefined(props.dateRange) ||
              isUndefined(props.dateRange.startDate) ||
              isUndefined(props.dateRange.endDate)
                ? ''
                : `${DateTime.fromJSDate(props.dateRange.startDate)
                    .toFormat(dateDisplayFormat)
                    .trim()} - ${DateTime.fromJSDate(props.dateRange.endDate)
                    .toFormat(dateDisplayFormat)
                    .trim()}
                      `
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton edge="end">
                    <materialIcons.DateRange />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
          <FormControl className={classes.dateRangePicker}>
            <DateRangePicker
              open={dateRangePickerOpen}
              toggle={toggleDateRangePicker}
              onChange={range => props.setDateRange(range)}
            />
          </FormControl>
        </Grid>
        <Grid item md={1} className={classes.aboutButtonGridItem}>
          <FormControl className={classes.minWidth210}>
            <Button onClick={openAboutModal} size="small">
              <HelpOutlineOutlined className={classes.helpIcon}></HelpOutlineOutlined>
              <p className={classes.aboutButtonText}>About this data</p>
            </Button>
          </FormControl>
          <AboutDataModal modalOpen={modalOpen} setModalOpen={setModalOpen} />
        </Grid>
      </Grid>
    </div>
  )
}
