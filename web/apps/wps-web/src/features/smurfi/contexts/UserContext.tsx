import React from 'react'

export interface UserContextType {
  name: string
  email: string
  phone: string
}

export const UserContext = React.createContext<UserContextType>({
  name: 'Matt MacDonald',
  email: 'BCWS.KFCFireWeather@gov.bc.ca',
  phone: '911'
})
