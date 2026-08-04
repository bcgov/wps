import { combineReducers } from '@reduxjs/toolkit'
import authenticateSlice from '@/slices/authenticationSlice'
import dataSlice from '@/slices/dataSlice'
import dateOfInterestSlice from '@/slices/dateOfInterestSlice'
import feedbackSlice from '@/slices/feedbackSlice'
import fireCentresSlice from '@/slices/fireCentresSlice'
import geolocationSlice from '@/slices/geolocationSlice'
import networkStatusSlice from '@/slices/networkStatusSlice'
import pushNotificationSlice from '@/slices/pushNotificationSlice'
import runParametersSlice from '@/slices/runParametersSlice'
import settingsSlice from '@/slices/settingsSlice'

export const rootReducer = combineReducers({
  fireCentres: fireCentresSlice,
  networkStatus: networkStatusSlice,
  geolocation: geolocationSlice,
  runParameters: runParametersSlice,
  authentication: authenticateSlice,
  feedback: feedbackSlice,
  data: dataSlice,
  dateOfInterest: dateOfInterestSlice,
  settings: settingsSlice,
  pushNotification: pushNotificationSlice
})
