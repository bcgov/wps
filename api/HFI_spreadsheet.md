# HFI Calculator Spreadsheet

## Caveats

This information was pulled from the sample HFI calculator spreadsheet "__20 HFI Workbook May 12-14.xlsx__", which is for the Coastal Fire Zone. Any possible variations between this and other fire zones have not been captured in this document.

Information for fuel type layer C6 is missing from the sample workbook.

These formulae are based on the formulae used in the sample workbook. The formulae listed in this document should be verified against other sources to confirm that formula interpolation has been performed correctly, and that the formula used in the reference workbook are correct. (Given the complex nature of some of the formulae, it is highly possible that mistakes have been made somewhere.)

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

### Rate of Spread (ROS)

The formula for ROS varies depending on the fuel layer type. The unit for ROS is m/min.

#### C1

$$
\text{ROS} = 90(1-\exp[-0.0649(\text{ISI})])^{4.5}(\exp[50 \times \ln{0.9} \times (\frac{1}{\text{BUI}} - \frac{1}{72})])
$$

#### C2

$$
\text{ROS} = 110(1-\exp[-0.0282(\text{ISI})])^{1.5}(\exp[50 \times \ln{0.7} \times (\frac{1}{\text{BUI}} - \frac{1}{64})])
$$

#### C3 and C3m

$$
\text{ROS} = 110(1-\exp[-0.0444(\text{ISI})])^{3}(\exp[50 \times \ln{0.75} \times (\frac{1}{\text{BUI}} - \frac{1}{62})])
$$

#### C4

$$
\text{ROS} = 110(1-\exp[-0.0293(\text{ISI})])^{1.5}(\exp[50 \times \ln{0.8} \times (\frac{1}{\text{BUI}} - \frac{1}{66})])
$$

#### C5

$$
\text{ROS} = 30(1-\exp[-0.0697(\text{ISI})])^{4}(\exp[50 \times \ln{0.8} \times (\frac{1}{\text{BUI}} - \frac{1}{56})])
$$

#### C7

$$
\text{ROS} = 45(1-\exp[-0.0305(\text{ISI})])^{2}(\exp[50 \times \ln{0.85} \times (\frac{1}{\text{BUI}} - \frac{1}{106})])
$$

#### S3

$$
\text{ROS} = 55(1-\exp[-0.0829(\text{ISI})])^{3.2}(\exp[50 \times \ln{0.75} \times (\frac{1}{\text{BUI}} - \frac{1}{31})])
$$

### Spread

$$
\text{Spread} = 60 \times \text{ROS}
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

Except there is an extra column in the spreadsheet for SFC of fuel type C7. The formula for C7 SFC is:

If FFMC < 70:
$$
\text{C7 SFC} = 1.5(1-\exp[-0.183(\text{BUI})])
$$

Else:
$$
\text{C7 SFC} = 2(1-\exp[-0.104(\text{FFMC} - 70)]) + 1.5(1-\exp[-0.183(\text{BUI})])
$$

### RSO

RSO is the critical surface fire rate of spread.

$$
\text{RSO} = \frac{\text{CSI}}{300 \times \text{SFC}}
$$

### CFB

CFB is the Crown Fraction Burned.

$$
\text{CFB} = 1 - \exp(-0.23(\text{ROS} - \text{RSO}))
$$

where ROS $\equiv$ Rate Of Spread

### HFI

_Buckle up, it's complicated_

At a high level, the formula for HFI calculation is

$$
\text{HFI} = 300 \times \text{TFC} \times \text{ROS}
$$
where TFC $\equiv$ Total Fuel Consumption.

$$
\text{TFC} = \text{SFC + CFC}
$$
where SFC $\equiv$ Surface Fuel Consumption and CFC $\equiv$ Crown Fuel Consumption.

$$
\text{CFC} = \text{CFL} \times \text{CFB}
$$
where CFL $\equiv$ Crown Fuel Load and CFB $\equiv$ Crown Fraction Burned. CFL is a set of constants based on fuel type.

We don't have the CFL constants available to us at the moment, so the following HFI equations have been inferred from the sample spreadsheet based on fuel layer type.

#### C1

If $(1.5(1-\exp[-0.23(\text{FFMC}-81)])) > 0$ AND $\frac{458}{1500(\text{ROS[C1]})(1-\exp[-0.0115 \times \text{BUI}])}<1$
$$
\text{HFI} = 225(1-\exp[-0.23(\text{ROS[C1]} - \frac{458}{450(1-\exp[-0.023(\text{FFMC}-81)])})]) + 1.5(1-\exp[-0.23(\text{FFMC} -81)])(\text{ROS[C1]})
$$

Else

$$
\text{HFI} = 1.5(1-\exp[-0.23(\text{FFMC}-81)])(\text{ROS[C1]})
$$

#### C2

#### C3

$$
\text{HFI} = M + 5(1-\exp[-0.0164 \times \text{BUI}]^{2.24})(\text{ROS})
$$

If $\frac{3667}{1500(\text{ROS})(1-\exp[-0.0164 \times \text{BUI}])^{2.24}} < 1$,

$$
\text{M} = 300(1.15)(1-\exp[-0.23(\text{ROS} - \frac{3667}{1500(1-\exp[-0.0164 \times \text{BUI}])})^{2.24}])
$$

Else $\text{M} = 0$.



### Head Fire Intensity Groups

| HFI  | Intensity Group |
|------|-----------------|
| <500        | 1        |
| $\geq$ 500  | 2        |
| $\geq$ 1000 | 3        |
| $\geq$ 2000 | 4        |
| $\geq$ 4000 | 5        |