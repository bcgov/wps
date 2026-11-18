import { Box, Button, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { BC_EXTENT } from '@wps/utils/constants'
import { Feature, View } from 'ol'
import { boundingExtent, buffer, type Extent, extend } from 'ol/extent'
import type { FeatureLike } from 'ol/Feature'
import { type Geometry, Point } from 'ol/geom'
import { Draw } from 'ol/interaction'
import type { DrawEvent } from 'ol/interaction/Draw'
import VectorLayer from 'ol/layer/Vector'
import { unByKey } from 'ol/Observable'
import { fromLonLat } from 'ol/proj'
import VectorSource from 'ol/source/Vector'
import { Circle, Fill, Stroke, Style } from 'ol/style'
import { useEffect, useRef, useState } from 'react'
import { areaLabel, clickStation, stationsInArea } from '@/features/climatology/components/map/stationSelection'
import { useSfmsMap } from '@/features/sfmsInsights/components/map/SFMSMap'

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))
// The margin around BC and the stations that panning and zooming out stop at, in map units. Map
// units shrink with latitude, so at 60° N this is about 150 km on the ground.
const VIEW_MARGIN = 300_000

/** What the map shows: BC and every station, some of which are outside it, such as in Yukon. */
export const stationsExtent = (stations: GeoJsonStation[]): Extent =>
  stations.reduce(
    (extent, { geometry }) => extend(extent, boundingExtent([fromLonLat(geometry.coordinates)])),
    [...bcExtent]
  )

/** A view where `current` is, that stops panning and zooming out a margin past BC and every station. */
const stationsView = (stations: GeoJsonStation[], current: View) =>
  new View({
    center: current.getCenter(),
    resolution: current.getResolution(),
    extent: buffer(stationsExtent(stations), VIEW_MARGIN),
    showFullExtent: true
  })

const stationStyle = new Style({
  image: new Circle({
    radius: 4,
    fill: new Fill({ color: '#3987e5' }),
    stroke: new Stroke({ color: '#ffffff', width: 1 })
  })
})
// A little larger than the others, with a white ring, so chosen stations stay apart when close.
const chosenStyle = new Style({
  image: new Circle({
    radius: 5,
    fill: new Fill({ color: '#0b0b0b' }),
    stroke: new Stroke({ color: '#ffffff', width: 1.5 })
  }),
  zIndex: 1
})
// OpenLayers' own look for drawing: a blue line on a white halo over a light wash. While drawing
// it marks the pointer with a dot as well, which looks like a station, so that is left out; the
// pointer is a crosshair instead.
const drawnLine = [
  new Style({ stroke: new Stroke({ color: '#ffffff', width: 5 }) }),
  new Style({ stroke: new Stroke({ color: '#0099ff', width: 3 }), fill: new Fill({ color: 'rgba(0, 153, 255, 0.1)' }) })
]
// A finished outline.
const areaStyle = drawnLine
const outlineFill = new Style({ fill: new Fill({ color: 'rgba(0, 153, 255, 0.1)' }) })
/** The look of an outline being drawn: the edges drawn so far over a light fill. OpenLayers also
 * closes the outline back to its start, which is left unstroked so it does not read as a line. */
const sketchStyle = (feature: FeatureLike) => {
  const type = feature.getGeometry()?.getType()
  if (type === 'Point') {
    return []
  }
  return type === 'Polygon' ? outlineFill : drawnLine
}

// How far a finished outline is smoothed, in screen pixels: enough to take the wobble out of a
// freehand trace, too little to move a clicked corner visibly.
const SMOOTHING_PIXELS = 3

export type StationMapMode = 'click' | 'draw'

export interface StationClimatologyLayersProps {
  stations: GeoJsonStation[]
  chosenCodes: number[]
  // The stations chosen on the map, and a name for them when they were chosen by drawing.
  onChoose: (codes: number[], label: string | null) => void
}

/** The weather stations, on the SFMS map: click them, or draw around them, to chart their climatology. */
const StationClimatologyLayers = ({ stations, chosenCodes, onChoose }: StationClimatologyLayersProps) => {
  const map = useSfmsMap()
  const [mode, setMode] = useState<StationMapMode>('click')
  const draw = useRef<Draw | null>(null)
  const [hovered, setHovered] = useState<{ name: string; x: number; y: number } | null>(null)

  const stationSource = useRef(new VectorSource<Feature<Point>>())
  const areaSource = useRef(new VectorSource<Feature<Geometry>>())
  // Read by OpenLayers' handlers, which are set up once.
  const latest = useRef({ stations, chosenCodes, onChoose, mode })
  latest.current = { stations, chosenCodes, onChoose, mode }

  const stationLayer = useRef(
    new VectorLayer({
      source: stationSource.current,
      zIndex: 60,
      style: feature => (latest.current.chosenCodes.includes(feature.get('code')) ? chosenStyle : stationStyle)
    })
  )

  // The stations and the drawn outline go on the map while this is shown, and come off with it.
  useEffect(() => {
    if (!map) {
      return
    }
    const areaLayer = new VectorLayer({ source: areaSource.current, style: areaStyle, zIndex: 55 })
    map.addLayer(areaLayer)
    map.addLayer(stationLayer.current)

    const stationAt = (pixel: number[]) =>
      map.forEachFeatureAtPixel(pixel, feature => feature, {
        layerFilter: layer => layer === stationLayer.current,
        hitTolerance: 6
      })

    const clickKey = map.on('singleclick', event => {
      const { mode: currentMode, chosenCodes: chosen, onChoose: choose } = latest.current
      if (currentMode !== 'click') {
        return
      }
      const feature = stationAt(event.pixel)
      if (feature) {
        areaSource.current.clear()
        choose(clickStation(chosen, feature.get('code'), event.originalEvent.shiftKey), null)
      }
    })
    const moveKey = map.on('pointermove', event => {
      if (event.dragging) {
        return
      }
      const feature = stationAt(event.pixel)
      // A name popping up under the pointer would get in the way of drawing.
      const named = feature && latest.current.mode === 'click'
      setHovered(named ? { name: feature.get('name'), x: event.pixel[0], y: event.pixel[1] } : null)
      const target = map.getTargetElement()
      if (target) {
        target.style.cursor = latest.current.mode === 'draw' ? 'crosshair' : feature ? 'pointer' : ''
      }
    })

    return () => {
      unByKey([clickKey, moveKey])
      map.removeLayer(areaLayer)
      map.removeLayer(stationLayer.current)
      const target = map.getTargetElement()
      if (target) {
        target.style.cursor = ''
      }
      // Back on the fire weather map, panning is free again and BC fills the map, as it starts.
      map.setView(new View({ center: map.getView().getCenter(), resolution: map.getView().getResolution() }))
      map.updateSize()
      map.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    }
  }, [map])

  // Panning and zooming out stop a margin past BC and the stations. The map is narrower beside the
  // charts, so it is fitted to them once they are known.
  const fitted = useRef(false)
  useEffect(() => {
    if (!map) {
      return
    }
    map.setView(stationsView(stations, map.getView()))
    if (stations.length > 0 && !fitted.current) {
      fitted.current = true
      map.updateSize()
      map.getView().fit(stationsExtent(stations), { padding: [70, 30, 30, 30] })
    }
  }, [map, stations])

  // One feature per station, named and coded for the handlers above.
  useEffect(() => {
    stationSource.current.clear()
    stationSource.current.addFeatures(
      stations.map(({ properties, geometry }) => {
        const feature = new Feature(new Point(fromLonLat(geometry.coordinates)))
        feature.setProperties({ code: properties.code, name: properties.name })
        return feature
      })
    )
  }, [stations])

  useEffect(() => {
    stationLayer.current.changed()
    if (chosenCodes.length === 0) {
      areaSource.current.clear()
    }
  }, [chosenCodes])

  // In draw mode, as in OpenLayers' polygon drawing: click to add corners and double-click to
  // finish, or hold Shift and drag to draw freehand. A plain drag still pans the map. The
  // stations inside the outline are chosen.
  useEffect(() => {
    if (!map || mode !== 'draw') {
      return
    }
    const interaction = new Draw({ source: areaSource.current, type: 'Polygon', style: sketchStyle, stopClick: true })
    interaction.on('drawstart', () => {
      areaSource.current.clear()
      setHovered(null)
    })
    interaction.on('drawend', (event: DrawEvent) => {
      const geometry = event.feature.getGeometry()
      if (!geometry) {
        return
      }
      const area = geometry.simplify((map.getView().getResolution() ?? 0) * SMOOTHING_PIXELS)
      event.feature.setGeometry(area)
      const codes = stationsInArea(latest.current.stations, area)
      latest.current.onChoose(codes, areaLabel(codes.length))
    })
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        interaction.abortDrawing()
      }
    }
    map.addInteraction(interaction)
    draw.current = interaction
    document.addEventListener('keydown', onKeyDown)
    const target = map.getTargetElement()
    if (target) {
      target.style.cursor = 'crosshair'
    }
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      map.removeInteraction(interaction)
      draw.current = null
      if (target) {
        target.style.cursor = ''
      }
    }
  }, [map, mode])

  return (
    <>
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          left: 48,
          right: 8,
          zIndex: 1,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 1,
          pointerEvents: 'none',
          '& > *': { pointerEvents: 'auto' }
        }}
      >
        <ToggleButtonGroup
          size="small"
          exclusive
          value={mode}
          onChange={(_, selected: StationMapMode | null) => selected && setMode(selected)}
          aria-label="How to choose stations"
          sx={{ bgcolor: 'background.paper' }}
        >
          <ToggleButton value="click">Click stations</ToggleButton>
          <ToggleButton value="draw">Draw an area</ToggleButton>
        </ToggleButtonGroup>
        {mode === 'draw' && (
          <Button
            size="small"
            variant="outlined"
            sx={{ bgcolor: 'background.paper' }}
            onClick={() => draw.current?.removeLastPoint()}
          >
            Undo point
          </Button>
        )}
        <Button
          size="small"
          variant="outlined"
          sx={{ bgcolor: 'background.paper' }}
          disabled={chosenCodes.length === 0}
          onClick={() => onChoose([], null)}
        >
          Clear
        </Button>
        <Typography variant="caption" sx={{ bgcolor: 'background.paper', paddingX: 1, borderRadius: 1 }}>
          {mode === 'click'
            ? 'Click a station to chart it. Shift+click adds or removes stations.'
            : 'Click to add corners and double-click to finish, or hold Shift and drag to draw freehand. Esc cancels.'}
        </Typography>
      </Box>
      {hovered && (
        <Box
          role="tooltip"
          sx={{
            position: 'absolute',
            left: hovered.x + 12,
            top: hovered.y + 12,
            zIndex: 2,
            pointerEvents: 'none',
            bgcolor: 'background.paper',
            boxShadow: 2,
            borderRadius: 1,
            paddingX: 1,
            paddingY: 0.5
          }}
        >
          <Typography variant="body2">{hovered.name}</Typography>
        </Box>
      )}
    </>
  )
}

export default StationClimatologyLayers
