import React, { useState, useContext, useEffect } from 'react'
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
  const [layer, setLayer] = useState<OLTileLayer | null>(null)

  useEffect(() => {
    if (!map) return

    const tileLayer = new OLTileLayer({
      source,
      zIndex,
      opacity
    })

    map.addLayer(tileLayer)
    tileLayer.setZIndex(zIndex)
    setLayer(tileLayer)

    return () => {
      if (map) {
        map.removeLayer(tileLayer)
      }
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!layer) return

    layer.setSource(source)
  }, [source]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

export default React.memo(TileLayer)
