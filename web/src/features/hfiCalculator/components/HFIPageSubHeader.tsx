import React, { SetStateAction } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { Container } from 'components/Container'
import { Button, FormControl } from '@material-ui/core'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'
import { isUndefined } from 'lodash'
import { FireCentre } from 'api/hfiCalcAPI'
import AboutDataModal from 'features/hfiCalculator/components/AboutDataModal'
import { HelpOutlineOutlined } from '@material-ui/icons'

const useStyles = makeStyles(theme => ({
  root: (props: Props) => ({
    maxHeight: 60,
    marginBottom: '1rem',
    paddingBottom: '1rem',
    paddingTop: '1rem',
    paddingLeft: props.padding,
    fontSize: '1.3rem',
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  }),
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
  }
}))

interface Props {
  padding?: string
  formControlClass: string
  fireCentres: Record<string, FireCentre>
  selectedFireCentre: FireCentre | undefined
  selectNewFireCentre: (newSelection: FireCentre | undefined) => void
  openAboutModal: () => void
  modalOpen: boolean
  setModalOpen: React.Dispatch<SetStateAction<boolean>>
}

export const HFIPageSubHeader: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)

  return (
    <div className={classes.root}>
      <Container>
        <FormControl className={props.formControlClass}>
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

        <FormControl className={classes.positionStyler}>
          <Button onClick={props.openAboutModal}>
            <HelpOutlineOutlined className={classes.helpIcon}></HelpOutlineOutlined>
            <p className={classes.aboutButtonText}>About this data</p>
          </Button>
        </FormControl>
        <AboutDataModal
          modalOpen={props.modalOpen}
          setModalOpen={props.setModalOpen}
        ></AboutDataModal>
      </Container>
    </div>
  )
}
