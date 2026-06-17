import { MapContext } from 'features/map/Map'
import OLTileLayer from 'ol/layer/Tile'
import type TileSource from 'ol/source/Tile'
import React, { useContext, useEffect, useState } from 'react'

interface Props {
  source: TileSource
  opacity?: number
  zIndex?: number
}

const TileLayer = ({ source, opacity = 1, zIndex = 0 }: Props) => {
  const map = useContext(MapContext)

  const [layer, setLayer] = useState<OLTileLayer<TileSource> | null>(null)

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — only re-run when map instance changes
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
  }, [map])

  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional — only re-run when source changes
  useEffect(() => {
    if (!layer) return

    layer.setSource(source)
  }, [source])

  return null
}

export default React.memo(TileLayer)
