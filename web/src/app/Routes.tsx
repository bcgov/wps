import React from 'react'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom'

import { HIDE_DISCLAIMER } from 'utils/env'
import AuthWrapper from 'features/auth/components/AuthWrapper'
import PercentileCalculatorPageWithDisclaimer from 'features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer'
import HfiCalculatorPage from 'features/hfiCalculator/pages/HfiCalculatorPage'
import CHainesPage from 'features/cHaines/pages/CHainesPage'
import {
  PERCENTILE_CALC_ROUTE,
  FIRE_WEATHER_ROUTE,
  MORECAST_ROUTE,
  HFI_CALC_ROUTE,
  C_HAINES_ROUTE,
  FIRE_BEHAVIOR_CALC_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  LANDING_PAGE_ROUTE,
  MORE_CAST_2_ROUTE
} from 'utils/constants'
import MoreCastPage from 'features/fireWeather/pages/MoreCastPage'
import { NoMatchPage } from 'features/fireWeather/pages/NoMatchPage'
import { FireBehaviourCalculator } from 'features/fbaCalculator/pages/FireBehaviourCalculatorPage'
import { FireBehaviourAdvisoryPage } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import LandingPage from 'features/landingPage/pages/LandingPage'
import MoreCast2Page from 'features/moreCast2/pages/MoreCast2Page'

const shouldShowDisclaimer = HIDE_DISCLAIMER === 'false' || HIDE_DISCLAIMER === undefined

const WPSRoutes: React.FunctionComponent = () => {
  return (
    <Router>
      <Routes>
        <Route path={LANDING_PAGE_ROUTE} element={<LandingPage />} />
        <Route
          path={PERCENTILE_CALC_ROUTE}
          element={<PercentileCalculatorPageWithDisclaimer showDisclaimer={shouldShowDisclaimer} />}
        />
        <Route path={FIRE_WEATHER_ROUTE} element={<Navigate to={MORECAST_ROUTE} />} />
        <Route
          path={MORECAST_ROUTE}
          element={
            <AuthWrapper>
              <MoreCastPage />
            </AuthWrapper>
          }
        />
        <Route
          path={HFI_CALC_ROUTE}
          element={
            <AuthWrapper>
              <HfiCalculatorPage />
            </AuthWrapper>
          }
        />
        <Route path={C_HAINES_ROUTE} element={<CHainesPage />} />

        <Route
          path={FIRE_BEHAVIOR_CALC_ROUTE}
          element={
            <AuthWrapper>
              <FireBehaviourCalculator />
            </AuthWrapper>
          }
        />
        <Route
          path={FIRE_BEHAVIOUR_ADVISORY_ROUTE}
          element={
            <AuthWrapper>
              <FireBehaviourAdvisoryPage />
            </AuthWrapper>
          }
        />
        <Route
          path={MORE_CAST_2_ROUTE}
          element={
            <AuthWrapper>
              <MoreCast2Page />
            </AuthWrapper>
          }
        />
        <Route path="*" element={<NoMatchPage />} />
      </Routes>
    </Router>
  )
}

export default React.memo(WPSRoutes)
