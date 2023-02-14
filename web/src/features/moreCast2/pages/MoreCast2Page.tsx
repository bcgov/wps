import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FormControl, Grid } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { FireCenter } from 'api/fbaAPI'
import { selectFireCenters } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { GeneralHeader } from 'components'
import FireCenterDropdown from 'components/FireCenterDropdown'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    borderTop: '1px solid black'
  },
  fireCenter: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh'
  }
}))

const MoreCast2Page = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)

  useEffect(() => {
    dispatch(fetchFireCenters())
    document.title = MORE_CAST_2_DOC_TITLE
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find(center => center.id.toString() == id)
    }
    if (fireCenters.length) {
      setFireCenter(findCenter(localStorage.getItem('preferredMoreCast2FireCenter')))
    }
  }, [fireCenters])

  useEffect(() => {
    if (isNull(fireCenter) || isUndefined(fireCenter)) {
      localStorage.removeItem('preferredMoreCast2FireCenter')
    }
    if (fireCenter?.id) {
      localStorage.setItem('preferredMoreCast2FireCenter', fireCenter?.id.toString())
    }
  }, [fireCenter])

  return (
    <div className={classes.root} data-testid="more-cast-2-page">
      <GeneralHeader padding="3em" spacing={0.985} title={MORE_CAST_2_NAME} productName={MORE_CAST_2_NAME} />
      <Grid container spacing={1}>
        <Grid item xs={2}>
          <FormControl className={classes.fireCenter}>
            <FireCenterDropdown
              fireCenterOptions={fireCenters}
              selectedFireCenter={fireCenter}
              setSelectedFireCenter={setFireCenter}
            />
          </FormControl>
        </Grid>
      </Grid>
      <div className={classes.content}></div>
    </div>
  )
}

export default React.memo(MoreCast2Page)
