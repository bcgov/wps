import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { Button, FormControl, Grid } from '@material-ui/core'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'
import { isUndefined } from 'lodash'
import { FireCentre } from 'api/hfiCalcAPI'
import AboutDataModal from 'features/hfiCalculator/components/AboutDataModal'
import { HelpOutlineOutlined } from '@material-ui/icons'
import DatePicker from 'components/DatePicker'
import { formControlStyles } from 'app/theme'

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
  dateOfInterestPicker: {
    marginLeft: 7,
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
  fireCentres: Record<string, FireCentre>
  dateOfInterest: string
  updateDate: (newDate: string) => void
  selectedFireCentre: FireCentre | undefined
  selectNewFireCentre: (newSelection: FireCentre | undefined) => void
}

export const HFIPageSubHeader: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)

  const [modalOpen, setModalOpen] = useState<boolean>(false)

  const openAboutModal = () => {
    setModalOpen(true)
  }

  return (
    <div className={classes.root}>
      <Grid
        container
        spacing={0}
        alignItems="center"
        direction="row"
        className={classes.gridContainer}
      >
        <Grid item md={3} lg={2}>
          <FormControl
            className={`${classes.dateOfInterestPicker} ${classes.minWidth210}`}
          >
            <DatePicker
              date={props.dateOfInterest}
              updateDate={props.updateDate}
              size={'small'}
            />
          </FormControl>
        </Grid>
        <Grid item md={3} lg={2}>
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
        <Grid
          item
          md={1}
          justifyContent="flex-end"
          className={classes.aboutButtonGridItem}
        >
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
