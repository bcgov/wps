import React, { useState } from 'react'
import { Button, FormControl, styled } from '@mui/material'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'
import { isUndefined } from 'lodash'
import { FireCentre } from 'api/hfiCalculatorAPI'
import AboutDataModal from 'features/hfiCalculator/components/AboutDataModal'
import { HelpOutlineOutlined } from '@mui/icons-material'
import { theme } from 'app/theme'
import { HFIResultResponse } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateRange } from 'components/dateRangePicker/types'
import PrepDateRangeSelector from 'features/hfiCalculator/components/PrepDateRangeSelector'
import LoggedInStatus from 'features/hfiCalculator/components/stationAdmin/LoggedInStatus'
import { selectAuthentication } from 'app/rootReducer'
import { useSelector } from 'react-redux'
import SignoutButton from 'features/auth/components/SignoutButton'

const PREFIX = 'HFIPageSubHeader'

const Root = styled('div', {
  name: `${PREFIX}-root`
})({
  background: theme.palette.primary.light,
  color: theme.palette.primary.contrastText,
  minHeight: 60,
  display: 'flex',
  flexWrap: 'nowrap',
  alignItems: 'center',
  paddingLeft: 25,
  paddingRight: 25,
  paddingTop: '0.5em',
  gap: 10
})

const WhiteHelpOutlineOutlined = styled(HelpOutlineOutlined, {
  name: `${PREFIX}-whiteHelpIcon`
})({
  fill: 'white'
})

const AboutButtonText = styled('p', {
  name: `${PREFIX}-aboutButtonText`
})({
  color: 'white',
  textDecoration: 'underline',
  fontWeight: 'bold',
  justifyContent: 'flex-end'
})

const AboutButtonGridItem = styled('div', {
  name: `${PREFIX}-aboutButtonGridItem`
})({
  marginLeft: 'auto',
  maxHeight: 56
})

const MinWidthFormControl = styled(FormControl, {
  name: `${PREFIX}-minWidthFormControl`
})({
  minWidth: 210
})

interface Props {
  padding?: string
  fireCentres: FireCentre[]
  setDateRange: (newDateRange: DateRange) => void
  selectedFireCentre: FireCentre | undefined
  result: HFIResultResponse | undefined
  selectNewFireCentre: (newSelection: FireCentre | undefined) => void
}

export const HFIPageSubHeader: React.FunctionComponent<Props> = (props: Props) => {
  const { isAuthenticated, roles, idir } = useSelector(selectAuthentication)
  const [modalOpen, setModalOpen] = useState<boolean>(false)

  const openAboutModal = () => {
    setModalOpen(true)
  }

  return (
    <Root>
      <FireCentreDropdown
        fireCentres={props.fireCentres}
        selectedValue={isUndefined(props.selectedFireCentre) ? null : { name: props.selectedFireCentre?.name }}
        onChange={props.selectNewFireCentre}
      />
      <PrepDateRangeSelector
        dateRange={props.result ? props.result.date_range : undefined}
        setDateRange={props.setDateRange}
      />
      <LoggedInStatus isAuthenticated={isAuthenticated} roles={roles} idir={idir} />
      <SignoutButton />
      <AboutButtonGridItem>
        <MinWidthFormControl>
          <Button onClick={openAboutModal} size="small">
            <WhiteHelpOutlineOutlined></WhiteHelpOutlineOutlined>
            <AboutButtonText>About this data</AboutButtonText>
          </Button>
        </MinWidthFormControl>
        <AboutDataModal modalOpen={modalOpen} setModalOpen={setModalOpen} />
      </AboutButtonGridItem>
    </Root>
  )
}
