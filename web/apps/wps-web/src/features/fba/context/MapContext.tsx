import type { Map as OlMap } from 'ol'
import React from 'react'

export const MapContext = React.createContext<OlMap | null>(null)
