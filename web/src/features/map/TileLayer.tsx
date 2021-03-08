import React, { useContext, useEffect } from 'react'
import TileSource from 'ol/source/Tile'
import OLTileLayer from 'ol/layer/Tile'

import { MapContext } from 'features/map/Map'

interface Props {
  source: TileSource
  opacity?: number
  zIndex?: number
}

const TileLayer = ({ source, opacity = 1, zIndex = 0 }: Props) => {
  const map = useContext(MapContext)!

  useEffect(() => {
    if (!map) return

    let tileLayer = new OLTileLayer({
      source,
      zIndex,
      opacity
    })

    map.addLayer(tileLayer)
    tileLayer.setZIndex(zIndex)

    return () => {
      if (map) {
        map.removeLayer(tileLayer)
      }
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

export default React.memo(TileLayer)
