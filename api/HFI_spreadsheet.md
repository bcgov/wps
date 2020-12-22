# HFI Calculator Spreadsheet

## Missing Data (that we definitely need)

- BUI values are used in HFI calculation. We don't have a reliable source for BUI info. Our 90th percentile calculator reports out BUI for a weather station, but it's based on data only up to the end of 2019. We will need access to the Phase 3 API in order to pull BUI data.
- We will need to know the fuel type layer(/s) for each weather station. Fuel type layers for some weather stations can presumably be pulled from the sample HFI calculator spreadsheet we've been given, but the spreadsheet only captures a small selection of all weather stations.

## Missing Data (that we might not need...?)

There are several data variables that are captured in the sample calculator spreadsheet that don't seem to actually factor into any calculation. Not sure if they're included as a nice-to-have for users, or if the information is important to FBANs & etc. making "manual" (non-calculated) decisions. These include:

- DMC and DC. Can we get them from Phase 3 API?
- station elevation

## Formulas and Reference Tables

The HFI value is based on fuel type and total fuel consumption. The calculation of total fuel consumption is based on a bunch of other calculations.

These are arranged in order of how the calculations must be performed.

### LB Ratio

| Wind Speed | LB Ratio |
|------------|----------|
| 0          | 1        |
| 5          | 1.1      |
| 10         | 1.5      |
| 15         | 2        |
| 20         | 2.6      |
| 25         | 3.3      |
| 30         | 3.8      |
| 35         | 4.4      |
| 40         | 4        |
| 45         | 5.6      |
| 50         | 6.1      |
| > 50       | 6.5      |

### Spread

$$
\text{Spread} = 60 \times \text{ROS (in m/min)}
$$

### 1 HR Fire Size

LB Ratio and Spread are necessary to calculate the 1 HR Fire Size.

$$
\text{1 HR Fire size} = \frac{\pi \times \text{spread}^2}{40,000 \times \text{LB ratio}}
$$ 

### CSI

| Fuel Type | CSI |
|-----------|-----|
| C1        | 602.8125177 |
| C2        | 1107.437309 |
| C3        | 4822.500141 |
| C3m       | 1705.01128 |
| C4        | 1705.011276 |
| C5        | 16275.93798 |
| C6        | 3947.156342 |
| C7        | 6739.648836 |

### SFC

$$
\text{SFC} = 1.5 \times (1-\exp[-0.23(\text{FFMC}-81)])
$$

### RSO

$$
\text{RSO} = \frac{\text{CSI}}{300 \times \text{SFC}}
$$

### CFB

$$
\text{CFB} = 1 - \exp(-0.23(\text{ROS} - \text{RSO}))
$$

where ROS $\equiv$ Rate Of Spread

### HFI

_Buckle up, it's complicated_

$$
\text{HFI} = (\text{multiplier} \times 300)(1.15 + (5(1-\exp[-0.0164 \times \text{BUI}]^{2.24})))(\text{ROS[fuel type]})
$$

where ROS[fuel type] indicates the Rate of Spread for the station's fuel type, and BUI is the Build Up Index.

To calculate the multiplier, first evaluate 

$$
\frac{\text{constant}}{1500(\text{ROS[fuel type]})((1-\exp[-0.0164\times\text{BUI}])^{2.24})}
$$

If this value is $\geq$ 1, the multiplier is 0 (and therefore HFI = 0).
If this value is < 1, 

$$
\text{multiplier} = 1-e^{-0.23 \times \text{ROS[fuel type]} - \frac{\text{constant}}{(1-\exp[-0.0164 \times \text{BUI}])^{2.24}}}
$$

Remember to plug the value of multiplier into the first equation.

### Head Fire Intensity Groups

| HFI  | Intensity Group |
|------|-----------------|
| <500        | 1        |
| $\geq$ 500  | 2        |
| $\geq$ 1000 | 3        |
| $\geq$ 2000 | 4        |
| $\geq$ 4000 | 5        |