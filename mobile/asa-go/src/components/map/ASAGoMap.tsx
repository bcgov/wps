import MapIconButton from "@/components/MapIconButton";
import ScaleContainer from "@/components/ScaleContainer";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { MapContext } from "@/context/MapContext";
import { fireShapeStyler } from "@/featureStylers";
import { extentsMap } from "@/fireCentreExtents";
import { fireZoneExtentsMap } from "@/fireZoneUnitExtents";
import {
  createBasemapLayer,
  createHFILayer,
  loadStaticPMTilesLayers,
  LOCAL_BASEMAP_LAYER_NAME,
} from "@/layerDefinitions";
import {
  AppDispatch,
  selectGeolocation,
  selectNetworkStatus,
  selectFireShapeAreas,
} from "@/store";
import { CENTER_OF_BC } from "@/utils/constants";
import MyLocationIcon from "@mui/icons-material/MyLocation";
import GpsOffIcon from "@mui/icons-material/GpsOff";
import { Box } from "@mui/material";
import { FireCenter, FireShape, RunType } from "api/fbaAPI";
import { cloneDeep, isNull, isUndefined } from "lodash";
import { DateTime } from "luxon";
import { Map, View } from "ol";
import { defaults as defaultControls } from "ol/control";
import {
  defaults as defaultInteractions,
  DblClickDragZoom,
} from "ol/interaction";
import ScaleLine from "ol/control/ScaleLine";
import { boundingExtent } from "ol/extent";
import TileLayer from "ol/layer/Tile";
import VectorTileLayer from "ol/layer/VectorTile";
import "ol/ol.css";
import { fromLonLat } from "ol/proj";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { BC_EXTENT } from "utils/constants";
import UserLocationIndicator from "@/components/map/LocationIndicator";
import { startWatchingLocation } from "@/slices/geolocationSlice";

// used for setting the initial map extent
const bcExtent = boundingExtent(BC_EXTENT.map((coord) => fromLonLat(coord)));

// used for bounding the map extent, limit panning to BC + buffer
const buffer = 1_500_000;
const BC_FULL_MAP_EXTENT_3857 = [
  bcExtent[0] - buffer,
  bcExtent[1] - buffer,
  bcExtent[2] + buffer,
  bcExtent[3] + buffer,
];

export interface ASAGoMapProps {
  testId?: string;
  selectedFireCenter: FireCenter | undefined;
  selectedFireShape: FireShape | undefined;
  advisoryThreshold: number;
  zoomSource?: "fireCenter" | "fireShape";
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  runType: RunType | null;
  runDatetime: DateTime | null;
}

const ASAGoMap = (props: ASAGoMapProps) => {
  const dispatch: AppDispatch = useDispatch();

  // selectors & hooks
  const { position, error, loading } = useSelector(selectGeolocation);
  const { networkStatus } = useSelector(selectNetworkStatus);

  // state
  const [map, setMap] = useState<Map | null>(null);
  const [scaleVisible, setScaleVisible] = useState<boolean>(true);
  const { fireShapeAreas } = useSelector(selectFireShapeAreas);
  const [basemapLayer] = useState<TileLayer>(createBasemapLayer());
  const [localBasemapVectorLayer, setLocalBasemapVectorLayer] =
    useState<VectorTileLayer>(() => {
      const layer = new VectorTileLayer();
      layer.set("name", LOCAL_BASEMAP_LAYER_NAME);
      return layer;
    });
  const [centerOnLocation, setCenterOnLocation] = useState<boolean>(false);

  const [fireZoneFileLayer] = useState<VectorTileLayer>(
    new VectorTileLayer({
      style: fireShapeStyler(
        cloneDeep(fireShapeAreas),
        props.advisoryThreshold,
        true
      ),
      zIndex: 53,
      properties: { name: "fireShapeVector" },
    })
  );

  const mapRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const scaleRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;

  // hfi layer ref, used to add/remove it from map
  const hfiLayerRef = useRef<VectorTileLayer | null>(null);

  const removeLayerByName = (map: Map, layerName: string) => {
    const layer = map
      .getLayers()
      .getArray()
      .find((l) => l.getProperties()?.name === layerName);
    if (layer) {
      map.removeLayer(layer);
    }
  };

  /**
   *
   * - If location tracking is not active, dispatches an action to start tracking.
   * - Sets a flag to center the map on the user's location upon update.
   * - If location tracking is already active and we have a position,
   *   it centers the map on the user's current position.
   */
  const handleLocationButtonClick = async () => {
    if (!map) return;

    if (!position || error) {
      dispatch(startWatchingLocation());
      setCenterOnLocation(true); // center map when position arrives
      return;
    }
    const pos = fromLonLat([
      position.coords.longitude,
      position.coords.latitude,
    ]);
    map.getView().animate({
      center: pos,
      zoom: 7.5,
      duration: 1000,
    });
  };

  // center map when position is updated after requesting location
  useEffect(() => {
    if (centerOnLocation && position && map) {
      const pos = fromLonLat([
        position.coords.longitude,
        position.coords.latitude,
      ]);
      map.getView().animate({
        center: pos,
        zoom: 7.5,
        duration: 1000,
      });
      setCenterOnLocation(false); // Reset flag
    }
  }, [centerOnLocation, position, map]);

  useEffect(() => {
    // zoom to fire center or whole province
    if (!map) return;

    if (props.selectedFireCenter && props.zoomSource === "fireCenter") {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name);
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent, {
          duration: 400,
          padding: [50, 50, 50, 50],
        });
      }
    } else if (!props.selectedFireCenter) {
      // reset map view to full province
      map.getView().fit(bcExtent, { duration: 600, padding: [50, 50, 50, 50] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireCenter]);

  useEffect(() => {
    // zoom to fire zone
    if (!map) return;

    if (props.selectedFireShape && props.zoomSource === "fireShape") {
      const zoneExtent = fireZoneExtentsMap.get(
        props.selectedFireShape.fire_shape_id.toString()
      );
      if (!isUndefined(zoneExtent)) {
        map.getView().fit(zoneExtent, {
          duration: 400,
          padding: [100, 100, 100, 100],
          maxZoom: 8,
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireShape]);

  useEffect(() => {
    fireZoneFileLayer.setStyle(
      fireShapeStyler(cloneDeep(fireShapeAreas), props.advisoryThreshold, true)
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fireShapeAreas]);

  useEffect(() => {
    if (!map) return;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    props.selectedFireCenter,
    props.selectedFireShape,
    fireShapeAreas,
    props.advisoryThreshold,
  ]);

  useEffect(() => {
    // Toggle basemap visibility based on network connection status.
    if (networkStatus.connected === true) {
      localBasemapVectorLayer.setVisible(false);
      basemapLayer.setVisible(true);
    } else {
      basemapLayer.setVisible(false);
      localBasemapVectorLayer.setVisible(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkStatus]);

  useEffect(() => {
    // The locally cached basemap pmtiles layer loads async, so add it
    // to the map once it is loaded and state updated.
    if (isNull(map) || isNull(localBasemapVectorLayer)) {
      return;
    }
    if (networkStatus.connected) {
      localBasemapVectorLayer.setVisible(false);
    }
    // Remove the placeholder VTL and then add the new localBasemapVectorLayer
    removeLayerByName(map, LOCAL_BASEMAP_LAYER_NAME);
    map.addLayer(localBasemapVectorLayer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localBasemapVectorLayer]);

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return;

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new Map({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC),
        extent: BC_FULL_MAP_EXTENT_3857,
      }),
      layers: [],
      overlays: [],
      controls: defaultControls({
        zoom: false,
      }),
      interactions: defaultInteractions({
        doubleClickZoom: true,
      }).extend([new DblClickDragZoom()]),
    });
    mapObject.setTarget(mapRef.current);

    const scaleBar = new ScaleLine({});
    scaleBar.setTarget(scaleRef.current);
    mapObject.addControl(scaleBar);

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] });

    setMap(mapObject);

    loadStaticPMTilesLayers(
      mapObject,
      fireZoneFileLayer,
      props.selectedFireCenter,
      props.selectedFireShape,
      setLocalBasemapVectorLayer
    );

    mapObject.addLayer(basemapLayer);

    const setScalelineVisibility = () => {
      setScaleVisible(true);
    };

    // Make the scale line visible when the user zooms in/out
    mapObject.getView().on("change:resolution", setScalelineVisibility);
    return () => {
      mapObject.removeControl(scaleBar);
      mapObject.getView().un("change:resolution", setScalelineVisibility);
      mapObject.setTarget("");
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return;
    if (isNull(props.runType) || isNull(props.runDatetime)) {
      if (hfiLayerRef.current) {
        map.removeLayer(hfiLayerRef.current);
        hfiLayerRef.current = null;
      }
      return;
    }

    let isMounted = true;
    (async () => {
      let hfiLayer: VectorTileLayer | null = null;
      if (!isNull(props.runType) && !isNull(props.runDatetime)) {
        hfiLayer = await createHFILayer({
          filename: "hfi.pmtiles",
          for_date: props.date,
          run_type: props.runType,
          run_date: props.runDatetime,
        });
      }

      // remove previous HFI layer
      if (hfiLayerRef.current) {
        map.removeLayer(hfiLayerRef.current);
      }
      if (hfiLayer && isMounted) {
        map.addLayer(hfiLayer);
        hfiLayerRef.current = hfiLayer;
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [map, props.runType, props.runDatetime, props.date]);

  return (
    <MapContext.Provider value={map}>
      <Box
        ref={mapRef}
        data-testid="fba-map"
        sx={{
          display: "flex",
          flex: 1,
          position: "relative",
          backgroundColor: "grey.300",
        }}
      >
        <UserLocationIndicator map={map} position={position} error={error} />

        <Box
          sx={{
            position: "absolute",
            left: "8px",
            bottom: "8px",
            zIndex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 1,
          }}
        >
          <MapIconButton
            onClick={handleLocationButtonClick}
            icon={error ? <GpsOffIcon color="error" /> : <MyLocationIcon />}
            testid="location-button"
            loading={loading}
          />
          <TodayTomorrowSwitch date={props.date} setDate={props.setDate} />
        </Box>
        <ScaleContainer
          visible={scaleVisible}
          setVisible={setScaleVisible}
          ref={scaleRef}
        />
      </Box>
    </MapContext.Provider>
  );
};

export default React.memo(ASAGoMap);
