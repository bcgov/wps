import React from "react";
import { Map } from "ol";

export const MapContext = React.createContext<Map | null>(null);

export const useMapContext = () => {
  const context = React.useContext(MapContext);
  return context;
};