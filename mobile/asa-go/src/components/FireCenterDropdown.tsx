import { MenuItem, Select, SelectChangeEvent, Typography } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import React from "react";

export interface FireCenterDropdownProps {
  selectedFireCenter?: FireCenter;
  fireCenterOptions: FireCenter[];
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const FireCenterDropdown = ({
  fireCenterOptions,
  selectedFireCenter,
  setSelectedFireCenter,
  setSelectedFireShape,
}: FireCenterDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<string>): void => {
    const selectedName = event.target.value;
    const selected = fireCenterOptions.find((fc) => fc.name === selectedName);
    setSelectedFireShape(undefined);
    setSelectedFireCenter(selected ?? undefined);
  };

  const getSelectedDisplay = (selected: FireCenter | undefined) => {
    if (!selected) {
      return (
        <Typography sx={{ color: "text.disabled" }}>
          Select Fire Centre
        </Typography>
      );
    }
    return selected.name;
  };

  return (
    <Select
      data-testid="fire-center-dropdown"
      value={selectedFireCenter?.name ?? ""}
      onChange={handleChange}
      displayEmpty
      renderValue={() => getSelectedDisplay(selectedFireCenter)}
    >
      {fireCenterOptions.map((option) => (
        <MenuItem key={option.name} value={option.name}>
          {option.name}
        </MenuItem>
      ))}
    </Select>
  );
};

export default React.memo(FireCenterDropdown);
