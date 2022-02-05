import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { Button, FormControl, Grid } from '@material-ui/core'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'
import { isUndefined } from 'lodash'
import { FireCentre } from 'api/hfiCalcAPI'
import AboutDataModal from 'features/hfiCalculator/components/AboutDataModal'
import { HelpOutlineOutlined } from '@material-ui/icons'
import DatePicker from 'components/DatePicker'

const useStyles = makeStyles(theme => ({
  root: {
    maxHeight: 60,
    marginBottom: '1rem',
    paddingBottom: '1rem',
    paddingTop: '1rem',
    paddingLeft: '1rem',
    fontSize: '1.3rem',
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
    alignContent: 'center'
  },
  positionStyler: {
    position: 'absolute',
    right: '20px'
  },
  helpIcon: {
    fill: 'white'
  },
  aboutButtonText: {
    color: 'white',
    textDecoration: 'underline',
    fontWeight: 'bold'
  },
  dateOfInterestPicker: {
    marginLeft: '7px',
    '& .MuiOutlinedInput-notchedOutline': {
      borderColor: 'white'
    },
    '& .MuiOutlinedInput-input': {
      color: 'white'
    },
    '& .PrivateNotchedOutline-legendLabelled-25': {
      color: 'white'
    },
    '& .MuiIconButton-root': {
      color: 'white'
    }
  }
}))

interface Props {
  padding?: string
  formControlClass: string
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
      <Grid container spacing={0}>
        <Grid item md={3}>
          <FormControl className={classes.dateOfInterestPicker}>
            <DatePicker
              date={props.dateOfInterest}
              updateDate={props.updateDate}
              size={'small'}
            />
          </FormControl>
        </Grid>
        <Grid item md={3}>
          <FormControl>
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
        <Grid item md={4}>
          {/* empty Grid item for spacing */}
        </Grid>

        <Grid item md={2} justifyContent="flex-end">
          <FormControl>
            <Button onClick={openAboutModal} size="small">
              <HelpOutlineOutlined className={classes.helpIcon}></HelpOutlineOutlined>
              <p className={classes.aboutButtonText}>About this data</p>
            </Button>
          </FormControl>
          <AboutDataModal
            modalOpen={modalOpen}
            setModalOpen={setModalOpen}
          ></AboutDataModal>
        </Grid>
      </Grid>
    </div>
  )
}
