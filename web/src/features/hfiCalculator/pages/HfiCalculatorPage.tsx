import React, { useState, useEffect } from 'react'
import { Button, Container, ErrorBoundary, GeneralHeader, PageTitle } from 'components'
import DatePicker from 'components/DatePicker'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import { fetchHFIDailies } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIDailies,
  selectHFIStations,
  selectHFIStationsLoading
} from 'app/rootReducer'
import { CircularProgress, FormControl, makeStyles, Tooltip } from '@material-ui/core'
import {
  FileCopyOutlined,
  CheckOutlined,
  InfoOutlined,
  HelpOutlineOutlined
} from '@material-ui/icons'
import { getDateRange } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { AboutDataModal } from 'features/hfiCalculator/components/AboutDataModal'
import { FormatTableAsCSV } from 'features/hfiCalculator/FormatTableAsCSV'
import { PST_UTC_OFFSET } from 'utils/constants'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  helpIcon: {
    fill: theme.palette.primary.main
  },
  copyToClipboardInfoIcon: {
    marginLeft: '3px'
  },
  clipboardIcon: {
    marginRight: '3px'
  },
  aboutButtonText: {
    color: theme.palette.primary.main,
    textDecoration: 'underline',
    fontWeight: 'bold'
  },
  positionStyler: {
    position: 'absolute',
    right: '20px'
  }
}))

const clipboardCopySuccessDuration = 2000 // milliseconds

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const [isWeeklyView, toggleTableView] = useState(false)
  const [modalOpen, setModalOpen] = useState<boolean>(false)

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now()
      .setZone('UTC' + PST_UTC_OFFSET)
      .toISO()
  )

  const [isCopied, setIsCopied] = useState(false)

  const refreshView = () => {
    //Slice being used to format the time zone/hours out of the date so the api call can be made
    const { start, end } = getDateRange(isWeeklyView, dateOfInterest.slice(0, 10))
    dispatch(fetchHFIStations())
    dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))
  }

  const updateDate = (date: string) => {
    /*This needs to be done in order for timezone to function correctly and not have the 
    date picker display the incorrect date*/
    date = `${date}T00:00:00-08:00`
    setDateOfInterest(date)
    refreshView()
  }

  const openAboutModal = () => {
    setModalOpen(true)
  }

  const copyTable = () => {
    if (isWeeklyView) {
      const weeklyViewAsString = FormatTableAsCSV.exportWeeklyRowsAsStrings(
        fireCentres,
        dailies
      )
      navigator.clipboard.writeText(weeklyViewAsString)
    } else {
      const dailyViewAsString = FormatTableAsCSV.exportDailyRowsAsStrings(
        fireCentres,
        dailies
      )
      navigator.clipboard.writeText(dailyViewAsString)
    }
    setIsCopied(true)
  }

  useEffect(() => {
    /**  this logic is copied from
     https://github.com/danoc/react-use-clipboard/blob/master/src/index.tsx 
     (the react-use-clipboard package was too restrictive for our needs, but the logic for
      having a timeout on the copy success message is helpful for us)
    */
    if (isCopied) {
      const id = setTimeout(() => {
        setIsCopied(false)
      }, clipboardCopySuccessDuration)

      return () => {
        clearTimeout(id)
      }
    }
  }, [isCopied])

  useEffect(() => {
    refreshView()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    refreshView()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isWeeklyView])

  return (
    <main data-testid="hfi-calculator-page">
      <GeneralHeader
        padding="3em"
        spacing={0.985}
        title="Predictive Services Unit"
        productName="HFI Calculator"
      />
      <PageTitle maxWidth={false} padding="1rem" title="HFI Calculator" />
      {loading || stationDataLoading ? (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      ) : (
        <Container maxWidth={'xl'}>
          <FormControl className={classes.formControl}>
            <DatePicker date={dateOfInterest} updateDate={updateDate} />
          </FormControl>

          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles
              isWeeklyView={isWeeklyView}
              toggleTableView={toggleTableView}
            />
          </FormControl>

          <FormControl className={classes.formControl}>
            {isCopied ? (
              <Button>
                <CheckOutlined />
                Copied!
              </Button>
            ) : (
              <Button onClick={copyTable}>
                <FileCopyOutlined className={classes.clipboardIcon} />
                Copy Data to Clipboard
                <Tooltip
                  title={
                    'You can paste all table data in Excel. To format: go to the Data tab, use Text to Columns > Delimited > Comma.'
                  }
                >
                  <InfoOutlined className={classes.copyToClipboardInfoIcon} />
                </Tooltip>
              </Button>
            )}
          </FormControl>

          <FormControl className={classes.positionStyler}>
            <Button onClick={openAboutModal}>
              <HelpOutlineOutlined className={classes.helpIcon}></HelpOutlineOutlined>
              <p className={classes.aboutButtonText}>About this data</p>
            </Button>
          </FormControl>
          <AboutDataModal
            modalOpen={modalOpen}
            setModalOpen={setModalOpen}
          ></AboutDataModal>

          <ErrorBoundary>
            <ViewSwitcher
              isWeeklyView={isWeeklyView}
              fireCentres={fireCentres}
              dailies={dailies}
              dateOfInterest={dateOfInterest}
            />
          </ErrorBoundary>
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
