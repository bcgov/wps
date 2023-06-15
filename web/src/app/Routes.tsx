import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom'

import { HIDE_DISCLAIMER } from 'utils/env'
import AuthWrapper from 'features/auth/components/AuthWrapper'
const PercentileCalculatorPageWithDisclaimer = lazy(
  () => import('features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer')
)
const HfiCalculatorPage = lazy(() => import('features/hfiCalculator/pages/HfiCalculatorPage'))
const CHainesPage = lazy(() => import('features/cHaines/pages/CHainesPage'))
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
const MoreCastPage = lazy(() => import('features/fireWeather/pages/MoreCastPage'))
import { NoMatchPage } from 'features/fireWeather/pages/NoMatchPage'
const FireBehaviourCalculator = lazy(() => import('features/fbaCalculator/pages/FireBehaviourCalculatorPage'))
const FireBehaviourAdvisoryPage = lazy(() => import('features/fba/pages/FireBehaviourAdvisoryPage'))
const LandingPage = lazy(() => import('features/landingPage/pages/LandingPage'))
const MoreCast2Page = lazy(() => import('features/moreCast2/pages/MoreCast2Page'))
import MoreCast2AuthWrapper from 'features/auth/components/MoreCast2AuthWrapper'

const shouldShowDisclaimer = HIDE_DISCLAIMER === 'false' || HIDE_DISCLAIMER === undefined

const WPSRoutes: React.FunctionComponent = () => {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
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
                <MoreCast2AuthWrapper>
                  <MoreCast2Page />
                </MoreCast2AuthWrapper>
              </AuthWrapper>
            }
          />
          <Route path="*" element={<NoMatchPage />} />
        </Routes>
      </Suspense>
    </Router>
  )
}

export default React.memo(WPSRoutes)
