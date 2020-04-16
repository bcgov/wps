import React from 'react'
import {
  BrowserRouter as Router,
  Route,
  Switch,
  Redirect
} from 'react-router-dom'

import { FireWeatherPage } from 'features/fireWeather/FireWeatherPage'
import { FWICalculatorPageWithDisclaimer } from 'features/fwiCalculator/FWICalculatorPageWithDisclaimer'

const NoMatch = () => <div>Page not found.</div>

const shouldShowDisclaimer = process.env.REACT_APP_HIDE_DISCLAIMER === undefined

export const Routes = () => {
  return (
    <Router>
      <Switch>
        <Redirect exact from="/" to="/percentile-calculator" />

        <Route path="/percentile-calculator">
          <FWICalculatorPageWithDisclaimer
            showDisclaimer={shouldShowDisclaimer}
          />
        </Route>

        <Route path="/fire-weather">
          <FireWeatherPage />
        </Route>

        <Route>
          <NoMatch />
        </Route>
      </Switch>
    </Router>
  )
}
