import React from 'react'
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom'

import { HIDE_DISCLAIMER } from 'utils/env'
import AuthWrapper from 'features/auth/AuthWrapper'
import PercentileCalculatorPageWithDisclaimer from 'features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer'
import HfiCalculatorPage from 'features/hfiCalculator/pages/HfiCalculatorPage'
import CHainesPage from 'features/cHaines/pages/CHainesPage'
import {
  PERCENTILE_CALC_ROUTE,
  FIRE_WEATHER_ROUTE,
  MORECAST_ROUTE,
  HFI_CALC_ROUTE,
  C_HAINES_ROUTE,
} from 'utils/constants'
import MoreCastPage from 'features/fireWeather/pages/MoreCastPage'
import { NoMatchPage } from 'features/fireWeather/pages/NoMatchPage'

const shouldShowDisclaimer = HIDE_DISCLAIMER === 'false' || HIDE_DISCLAIMER === undefined
const shouldAuthenticate =
  process.env.NODE_ENV === 'production' || window.Cypress === undefined

const Routes: React.FunctionComponent = () => {
  return (
    <Router>
      <Switch>
        <Redirect exact from="/" to={PERCENTILE_CALC_ROUTE} />

        <Route path={PERCENTILE_CALC_ROUTE}>
          <PercentileCalculatorPageWithDisclaimer showDisclaimer={shouldShowDisclaimer} />
        </Route>

        <Redirect from={FIRE_WEATHER_ROUTE} to={MORECAST_ROUTE} />
        <Route path={MORECAST_ROUTE}>
          <AuthWrapper shouldAuthenticate={shouldAuthenticate}>
            <MoreCastPage />
          </AuthWrapper>
        </Route>

        <Route path={HFI_CALC_ROUTE}>
          <AuthWrapper shouldAuthenticate={shouldAuthenticate}>
            <HfiCalculatorPage />
          </AuthWrapper>
        </Route>

        <Route path={C_HAINES_ROUTE}>
          <CHainesPage />
        </Route>

        <Route>
          <NoMatchPage />
        </Route>
      </Switch>
    </Router>
  )
}

export default React.memo(Routes)
