import { Autocomplete, TextField } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import { isEqual, isNull } from "lodash";
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

const FireCenterDropdown = (props: FireCenterDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedFireCenter, value)) {
      props.setSelectedFireShape(undefined);
      props.setSelectedFireCenter(value);
    }
    if (isNull(value)) {
      localStorage.removeItem("preferredFireCenter");
    }
  };

  return (
    <Autocomplete
      data-testid={`fire-center-dropdown`}
      options={props.fireCenterOptions}
      getOptionLabel={(option) => option?.name}
      renderInput={(params) => (
        <TextField {...params} label="Select Fire Centre" variant="outlined" />
      )}
      onChange={changeHandler}
      value={props.selectedFireCenter || null}
    />
  );
};

export default React.memo(FireCenterDropdown);
