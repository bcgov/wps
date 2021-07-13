""" Call Java REDapp code.
"""
from datetime import datetime
import jnius_config
# import jnius - importing jnius on this level causes an segmentation fault.
from app import config

jnius_config.set_classpath(config.get('CLASSPATH'))


class UnmappedFuelType(Exception):
    """ Raised for fuel types that don't have an index mapping """


def red_app_fuel_type_map(fuel_type: str):
    """
    This is messy. REDapp has a combo box with fuel types, which it then maps
    to a fuel type index.

    new FuelValue(Cwfgm_Fuel_C1.class, "C-1:  Spruce-Lichen Woodland"),
    new FuelValue(Cwfgm_Fuel_C2.class, "C-2:  Boreal Spruce"),
    new FuelValue(Cwfgm_Fuel_C3.class, "C-3:  Mature Jack or Lodgepole Pine"),
    new FuelValue(Cwfgm_Fuel_C4.class, "C-4:  Immature Jack or Lodgepole Pine"),
    new FuelValue(Cwfgm_Fuel_C5.class, "C-5:  Red and White Pine"),
    new FuelValue(Cwfgm_Fuel_C6.class, "C-6:  Conifer Plantation"),
    new FuelValue(Cwfgm_Fuel_C7.class, "C-7:  Ponderosa Pine / Douglas Fir"),
    new FuelValue(Cwfgm_Fuel_D1.class, "D-1:  Leafless Aspen"),
    new FuelValue(Cwfgm_Fuel_D2.class, "D-2:  Green Aspen (w/ BUI Thresholding)"),
    new FuelValue(Cwfgm_Fuel_D1D2.class, "D-1/D-2:  Aspen"),
    new FuelValue(Cwfgm_Fuel_M1.class, "M-1:  Boreal Mixedwood - Leafless"),
    new FuelValue(Cwfgm_Fuel_M2.class, "M-2:  Boreal Mixedwood - Green"),
    new FuelValue(Cwfgm_Fuel_M1M2.class, "M-1/M-2:  Boreal Mixedwood"),
    new FuelValue(Cwfgm_Fuel_M3.class, "M-3:  Dead Balsam Fir / Mixedwood - Leafless"),
    new FuelValue(Cwfgm_Fuel_M4.class, "M-4:  Dead Balsam Fir / Mixedwood - Green"),
    new FuelValue(Cwfgm_Fuel_M3M4.class, "M-3/M-4:  Dead Balsam Fir / Mixedwood"),
    new FuelValue(Cwfgm_Fuel_O1a.class, "O-1a:  Matted Grass"),
    new FuelValue(Cwfgm_Fuel_O1b.class, "O-1b:  Standing Grass"),
    new FuelValue(Cwfgm_Fuel_O1ab.class, "O-1ab:  Grass"),
    new FuelValue(Cwfgm_Fuel_S1.class, "S-1:  Jack or Lodgepole Pine Slash"),
    new FuelValue(Cwfgm_Fuel_S2.class, "S-2:  White Spruce / Balsam Slash"),
    new FuelValue(Cwfgm_Fuel_S3.class, "S-3:  Coastal Cedar / Hemlock / Douglas-Fir Slash") };

    comboIndexToFuel.put(Integer.valueOf(0), Integer.valueOf(0));
    comboIndexToFuel.put(Integer.valueOf(1), Integer.valueOf(1));
    comboIndexToFuel.put(Integer.valueOf(2), Integer.valueOf(2));
    comboIndexToFuel.put(Integer.valueOf(3), Integer.valueOf(3));
    comboIndexToFuel.put(Integer.valueOf(4), Integer.valueOf(4));
    comboIndexToFuel.put(Integer.valueOf(5), Integer.valueOf(5));
    comboIndexToFuel.put(Integer.valueOf(6), Integer.valueOf(6));
    comboIndexToFuel.put(Integer.valueOf(7), Integer.valueOf(7));
    comboIndexToFuel.put(Integer.valueOf(8), Integer.valueOf(8));
    comboIndexToFuel.put(Integer.valueOf(9), Integer.valueOf(10));
    comboIndexToFuel.put(Integer.valueOf(10), Integer.valueOf(11));
    comboIndexToFuel.put(Integer.valueOf(11), Integer.valueOf(13));
    comboIndexToFuel.put(Integer.valueOf(12), Integer.valueOf(14));
    comboIndexToFuel.put(Integer.valueOf(13), Integer.valueOf(16));
    comboIndexToFuel.put(Integer.valueOf(14), Integer.valueOf(17));
    comboIndexToFuel.put(Integer.valueOf(15), Integer.valueOf(18));
    comboIndexToFuel.put(Integer.valueOf(16), Integer.valueOf(19));
    comboIndexToFuel.put(Integer.valueOf(17), Integer.valueOf(20));
    comboIndexToFuel.put(Integer.valueOf(18), Integer.valueOf(21));

    combobox index -> fuel type index
    0:0 "C-1:  Spruce-Lichen Woodland"
    1:1 "C-2:  Boreal Spruce"
    2:2 "C-3:  Mature Jack or Lodgepole Pine"
    3:3 "C-4:  Immature Jack or Lodgepole Pine"
    4:4 "C-5:  Red and White Pine"
    5:5 "C-6:  Conifer Plantation"
    6:6 "C-7:  Ponderosa Pine / Douglas Fir"
    7:7 "D-1:  Leafless Aspen"
    8:8 "D-2:  Green Aspen (w/ BUI Thresholding)"
    9:10 "D-1/D-2:  Aspen"
    10:11 "M-1:  Boreal Mixedwood - Leafless"
    11:13 "M-2:  Boreal Mixedwood - Green"
    12:14 "M-1/M-2:  Boreal Mixedwood"
    13:16 "M-3:  Dead Balsam Fir / Mixedwood - Leafless"
    14:17 "M-4:  Dead Balsam Fir / Mixedwood - Green"
    15:18 "M-3/M-4:  Dead Balsam Fir / Mixedwood"
    16:19 "O-1a:  Matted Grass"
    17:20 "O-1b:  Standing Grass"
    18:21 "O-1ab:  Grass"
    19"S-1:  Jack or Lodgepole Pine Slash"
    20"S-2:  White Spruce / Balsam Slash"
    21"S-3:  Coastal Cedar / Hemlock / Douglas-Fir Slash"
    """
    fuel_type_map = {
        'C1': 0,
        'C2': 1,
        'C3': 2,
        'C4': 3,
        'C5': 4,
        'C6': 5,
        'C7': 6,
        'D1': 7,
        'D2': 8,
        # D1/D2: Aspen # we don't have this as a dropdown right now!
        'M1': 11,
        'M2': 13,
        # M1/M2: Boreal Mixedwood # we don't have this as a dropdown right now!
        'M3': 16,
        'M4': 17,
        # M3/M4: Dead Balsam Fir / Mixedwood # we don't have this as a dropdown right now!
        'O1A': 19,
        'O1B': 20,
        # O1ab: Grass # we don't have this as a dropdown right now!
        # 'S1': - no mapping
        # 'S2': - no mapping
        # 'S3': - no mapping
    }
    if fuel_type in fuel_type_map:
        return fuel_type_map[fuel_type]
    raise UnmappedFuelType(fuel_type)


def FBPCalculateStatisticsCOM(elevation: float,  # pylint: disable=invalid-name, too-many-arguments
                              latitude: float,
                              longitude: float,
                              time_of_interest: datetime,
                              fuel_type: str,
                              ffmc: float,
                              dmc: float,
                              dc: float,
                              bui: float,
                              wind_speed: float,
                              wind_direction: float,
                              percentage_conifer: float,
                              percentage_dead_balsam_fir: float,
                              grass_cure: float,
                              crown_base_height: float):
    """ Uses method FBPCalculateStatisticsCOM on class ca.cwfgm.fbp.FBPCalculations to calculate
    fire behaviour.

    public class FBPCalculations {
        public double ros_t;
        public double ros_eq;
        public double fros;
        public double bros;
        public double rso;
        public double hfi;
        public double ffi;
        public double bfi;
        public double area;
        public double perimeter;
        public double distanceHead;
        public double distanceFlank;
        public double distanceBack;
        public double lb;
        public double csi;
        public double cfb;
        public double sfc;
        public double tfc;
        public double cfc;
        public double isi;
        public double fmc;
        public double wsv;
        public double raz;
        public double conifMixedWood;
        public double deadBalsam;
        public double grassCuring;
        public double grassFuelLoad;
        public double crownBase;
        public double elapsedTime;
        public double ffmc;
        public double windSpeed;
        public double windDirection;
        public double bui;
        public double dmc;
        public double dc;
        public double slopeValue;
        public double aspect;
        public double latitude;
        public double longitude;
        public double elevation;
        public boolean acceleration;
        public boolean useCrownBaseHeight;
        public boolean useBui;
        public boolean useBuildup;
        public boolean useSlope;
        public boolean useGreenup;
        public int fuelType;
        public String fireDescription;
        public String headFireDescription;
        public String flankFireDescription;
        public String backFireDescription;

        public Calendar m_date;

        public boolean cfbPossible = true;

        public FBPCalculations() {
        initializeInputValues();
        initializeOutputValues();
        }
        public void FBPCalculateStatisticsCOM()
    }
    """
    # pylint: disable=too-many-locals
    # we have to do a late import, otherwise we get a segmentation fault.
    from jnius import autoclass  # pylint: disable=import-outside-toplevel
    Calendar = autoclass('java.util.Calendar')  # pylint: disable=invalid-name
    TimeZone = autoclass('java.util.TimeZone')  # pylint: disable=invalid-name
    FBPCalculations = autoclass('ca.cwfgm.fbp.FBPCalculations')  # pylint: disable=invalid-name

    if percentage_dead_balsam_fir is None:
        percentage_dead_balsam_fir = 0.0
    if grass_cure is None:
        grass_cure = 0.0

    fbp = FBPCalculations()
    fbp.elevation = elevation
    fbp.latitude = latitude
    fbp.longitude = longitude
    fbp.ffmc = ffmc
    fbp.dmc = dmc
    fbp.dc = dc
    fbp.useBui = True
    fbp.useBuildup = True
    fbp.bui = bui
    fbp.windSpeed = wind_speed
    fbp.windDirection = wind_direction
    fbp.fuelType = red_app_fuel_type_map(fuel_type)
    fbp.conifMixedWood = percentage_conifer
    fbp.deadBalsam = percentage_dead_balsam_fir
    fbp.grassCuring = grass_cure
    fbp.crownBase = crown_base_height
    # grassFuelLoad

    fbp.useSlope = False

    gmt = Calendar.getInstance(TimeZone.getTimeZone("GMT"))
    gmt.set(time_of_interest.year, time_of_interest.month, time_of_interest.day,
            time_of_interest.hour, time_of_interest.minute, time_of_interest.second)
    fbp.m_date = gmt

    fbp.FBPCalculateStatisticsCOM()

    return fbp


def get_class_FWICalculations():  # pylint: disable=invalid-name
    """
    Return Java class ca.cwfgm.fwi.FWICalculations

    public class FWICalculations {

        public double ystrdyFFMC;
        public double ystrdyDMC;
        public double ystrdyDC;
        public double noonTemp;
        public double noonRH;
        public double noonPrecip;
        public double noonWindSpeed;
        public double hrlyTemp;
        public double hrlyRH;
        public double hrlyPrecip;
        public double hrlyWindSpeed;
        public double dlyFFMC;
        public double dlyDMC;
        public double dlyDC;
        public double dlyISI;
        public double dlyBUI;
        public double dlyFWI;
        public double dlyDSR;
        public double hlyHFFMC;
        public double hlyHISI;
        public double hlyHFWI;
        public double prvhlyFFMC;
        public boolean calcHourly;
        public boolean useVanWagner;
        public boolean useLawsonPreviousHour = false;
        private WorldLocation wl;
        public Calendar m_date;
        public String m_init_timezone_code;

        public double getLatitude();
        public void setLatitude(double value);
        public double getLongitude();
        public void setLongitude(double value);

        public void setTimezone(WTimeSpan span);
        public void setDST(WTimeSpan span);

        public void FWICalculateDailyStatisticsCOM();
    """
    # we have to do a late import, otherwise we get a segmentation fault.
    from jnius import autoclass  # pylint: disable=import-outside-toplevel
    return autoclass('ca.cwfgm.fwi.FWICalculations')
