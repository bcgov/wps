import React from 'react'
import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import PercentIcon from '@mui/icons-material/Percent'
import PublicIcon from '@mui/icons-material/Public'
import WhatshotOutlinedIcon from '@mui/icons-material/WhatshotOutlined'
import {
  C_HAINES_NAME,
  C_HAINES_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_NAME,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  FIRE_BEHAVIOUR_CALC_NAME,
  FIRE_BEHAVIOR_CALC_ROUTE,
  HFI_CALC_NAME,
  HFI_CALC_ROUTE,
  MORE_CAST_NAME,
  MORECAST_ROUTE,
  PERCENTILE_CALC_NAME,
  PERCENTILE_CALC_ROUTE
} from 'utils/constants'

export const toolInfo = [
  {
    name: FIRE_BEHAVIOUR_ADVISORY_NAME,
    route: FIRE_BEHAVIOUR_ADVISORY_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <LocalFireDepartmentIcon color="primary" />
  },
  {
    name: C_HAINES_NAME,
    route: C_HAINES_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <PublicIcon color="primary" />
  },
  {
    name: FIRE_BEHAVIOUR_CALC_NAME,
    route: FIRE_BEHAVIOR_CALC_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <PercentIcon color="primary" />
  },
  {
    name: HFI_CALC_NAME,
    route: HFI_CALC_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <CalculateOutlinedIcon color="primary" />
  },
  {
    name: MORE_CAST_NAME,
    route: MORECAST_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <AirOutlinedIcon color="primary" />
  },
  {
    name: PERCENTILE_CALC_NAME,
    route: PERCENTILE_CALC_ROUTE,
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mattis pulvinar metus. Morbi sit amet lectus pellentesque, tempor arcu et, aliquet enim. Duis ipsum neque, hendrerit a pharetra id, convallis vel lectus. Morbi et molestie magna. Quisque dictum metus id metus laoreet gravida. Phasellus vel dolor ipsum. Duis tempus mollis augue.',
    icon: <WhatshotOutlinedIcon color="primary" />
  }
]
