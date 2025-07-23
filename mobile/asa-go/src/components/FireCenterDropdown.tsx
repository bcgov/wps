import { MenuItem, Select, SelectChangeEvent } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import React from "react";

interface FireCenterDropdownProps {
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

  return (
    <Select
      data-testid="fire-center-dropdown"
      value={selectedFireCenter?.name ?? ""}
      onChange={handleChange}
      displayEmpty
      renderValue={(selected) =>
        selected ? (
          selected
        ) : (
          <span style={{ color: "#aaa" }}>Select Fire Center</span>
        )
      }
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
