import { MenuItem, Select } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import { isEqual, isNil } from "lodash";
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
  const handleClick = (value: FireCenter) => {
    if (!isEqual(selectedFireCenter, value)) {
      setSelectedFireShape(undefined);
      setSelectedFireCenter(value);
    }
  };

  if (isNil(selectedFireCenter) && fireCenterOptions.length) {
    setSelectedFireCenter(fireCenterOptions[0]);
  }

  return (
    <Select value={selectedFireCenter?.name ?? ""}>
      {fireCenterOptions.map((option) => (
        <MenuItem
          key={option.name}
          value={option.name}
          onClick={() => handleClick(option)}
        >
          {option.name}
        </MenuItem>
      ))}
    </Select>
  );
};

export default React.memo(FireCenterDropdown);
