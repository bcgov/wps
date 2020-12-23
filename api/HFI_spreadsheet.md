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

<!-- $$
\text{ROS} = 90(1-\exp[-0.0649(\text{ISI})])^{4.5}(\exp[50 \times \ln{0.9} \times (\frac{1}{\text{BUI}} - \frac{1}{72})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%2090(1-%5Cexp%5B-0.0649(%5Ctext%7BISI%7D)%5D)%5E%7B4.5%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.9%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B72%7D)%5D)"></div>

#### C2

<!-- $$
\text{ROS} = 110(1-\exp[-0.0282(\text{ISI})])^{1.5}(\exp[50 \times \ln{0.7} \times (\frac{1}{\text{BUI}} - \frac{1}{64})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%20110(1-%5Cexp%5B-0.0282(%5Ctext%7BISI%7D)%5D)%5E%7B1.5%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.7%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B64%7D)%5D)"></div>

#### C3 and C3m

<!-- $$
\text{ROS} = 110(1-\exp[-0.0444(\text{ISI})])^{3}(\exp[50 \times \ln{0.75} \times (\frac{1}{\text{BUI}} - \frac{1}{62})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%20110(1-%5Cexp%5B-0.0444(%5Ctext%7BISI%7D)%5D)%5E%7B3%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.75%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B62%7D)%5D)"></div>

#### C4

<!-- $$
\text{ROS} = 110(1-\exp[-0.0293(\text{ISI})])^{1.5}(\exp[50 \times \ln{0.8} \times (\frac{1}{\text{BUI}} - \frac{1}{66})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%20110(1-%5Cexp%5B-0.0293(%5Ctext%7BISI%7D)%5D)%5E%7B1.5%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.8%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B66%7D)%5D)"></div>

#### C5

<!-- $$
\text{ROS} = 30(1-\exp[-0.0697(\text{ISI})])^{4}(\exp[50 \times \ln{0.8} \times (\frac{1}{\text{BUI}} - \frac{1}{56})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%2030(1-%5Cexp%5B-0.0697(%5Ctext%7BISI%7D)%5D)%5E%7B4%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.8%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B56%7D)%5D)"></div>

#### C7

<!-- $$
\text{ROS} = 45(1-\exp[-0.0305(\text{ISI})])^{2}(\exp[50 \times \ln{0.85} \times (\frac{1}{\text{BUI}} - \frac{1}{106})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%2045(1-%5Cexp%5B-0.0305(%5Ctext%7BISI%7D)%5D)%5E%7B2%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.85%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B106%7D)%5D)"></div>

#### S3

<!-- $$
\text{ROS} = 55(1-\exp[-0.0829(\text{ISI})])^{3.2}(\exp[50 \times \ln{0.75} \times (\frac{1}{\text{BUI}} - \frac{1}{31})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BROS%7D%20%3D%2055(1-%5Cexp%5B-0.0829(%5Ctext%7BISI%7D)%5D)%5E%7B3.2%7D(%5Cexp%5B50%20%5Ctimes%20%5Cln%7B0.75%7D%20%5Ctimes%20(%5Cfrac%7B1%7D%7B%5Ctext%7BBUI%7D%7D%20-%20%5Cfrac%7B1%7D%7B31%7D)%5D)"></div>

### Spread

<!-- $$
\text{Spread} = 60 \times \text{ROS}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BSpread%7D%20%3D%2060%20%5Ctimes%20%5Ctext%7BROS%7D"></div>

### 1 HR Fire Size

LB Ratio and Spread are necessary to calculate the 1 HR Fire Size.

<!-- $$
\text{1 HR Fire size} = \frac{\pi \times \text{spread}^2}{40,000 \times \text{LB ratio}}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7B1%20HR%20Fire%20size%7D%20%3D%20%5Cfrac%7B%5Cpi%20%5Ctimes%20%5Ctext%7Bspread%7D%5E2%7D%7B40%2C000%20%5Ctimes%20%5Ctext%7BLB%20ratio%7D%7D"></div> 

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

<!-- $$
\text{SFC} = 1.5 \times (1-\exp[-0.23(\text{FFMC}-81)])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BSFC%7D%20%3D%201.5%20%5Ctimes%20(1-%5Cexp%5B-0.23(%5Ctext%7BFFMC%7D-81)%5D)"></div>

Except there is an extra column in the spreadsheet for SFC of fuel type C7. The formula for C7 SFC is:

If FFMC < 70:
<!-- $$
\text{SFC}_{C7} = 1.5(1-\exp[-0.183(\text{BUI})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BSFC%7D_%7BC7%7D%20%3D%201.5(1-%5Cexp%5B-0.183(%5Ctext%7BBUI%7D)%5D)"></div>

Else:
<!-- $$
\text{SFC}_{C7} = 2(1-\exp[-0.104(\text{FFMC} - 70)]) + 1.5(1-\exp[-0.183(\text{BUI})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BSFC%7D_%7BC7%7D%20%3D%202(1-%5Cexp%5B-0.104(%5Ctext%7BFFMC%7D%20-%2070)%5D)%20%2B%201.5(1-%5Cexp%5B-0.183(%5Ctext%7BBUI%7D)%5D)"></div>


### RSO

RSO is the critical surface fire rate of spread.

<!-- $$
\text{RSO} = \frac{\text{CSI}}{300 \times \text{SFC}}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BRSO%7D%20%3D%20%5Cfrac%7B%5Ctext%7BCSI%7D%7D%7B300%20%5Ctimes%20%5Ctext%7BSFC%7D%7D"></div>

### CFB

CFB is the Crown Fraction Burned.

<!-- $$
\text{CFB} = 1 - \exp(-0.23(\text{ROS} - \text{RSO}))
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BCFB%7D%20%3D%201%20-%20%5Cexp(-0.23(%5Ctext%7BROS%7D%20-%20%5Ctext%7BRSO%7D))"></div>

where ROS = Rate Of Spread

### HFI

_Buckle up, it's complicated_

At a high level, the formula for HFI calculation is

<!-- $$
\text{HFI} = 300 \times \text{TFC} \times \text{ROS}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20300%20%5Ctimes%20%5Ctext%7BTFC%7D%20%5Ctimes%20%5Ctext%7BROS%7D"></div>
where TFC = Total Fuel Consumption.

<!-- $$
\text{TFC} = \text{SFC + CFC}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BTFC%7D%20%3D%20%5Ctext%7BSFC%20%2B%20CFC%7D"></div>
where SFC = Surface Fuel Consumption and CFC = Crown Fuel Consumption.

<!-- $$
\text{CFC} = \text{CFL} \times \text{CFB}
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BCFC%7D%20%3D%20%5Ctext%7BCFL%7D%20%5Ctimes%20%5Ctext%7BCFB%7D"></div>
where CFL = Crown Fuel Load and CFB = Crown Fraction Burned. CFL is a set of constants based on fuel type.


We don't have the CFL constants available to us at the moment, so the following HFI equations have been inferred from the sample spreadsheet based on fuel layer type.

#### C1

<!-- $$
\text{HFI} = \text{M} + 1.5 \times \text{ROS}(1-\exp[-0.23(\text{FFMC}-81)])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20%5Ctext%7BM%7D%20%2B%201.5%20%5Ctimes%20%5Ctext%7BROS%7D(1-%5Cexp%5B-0.23(%5Ctext%7BFFMC%7D-81)%5D)"></div>

If <!-- $(1.5(1-\exp[-0.23(\text{FFMC}-81)])) > 0$ --> <img src="https://render.githubusercontent.com/render/math?math=(1.5(1-%5Cexp%5B-0.23(%5Ctext%7BFFMC%7D-81)%5D))%20%3E%200"> AND <!-- $\frac{458}{1500(\text{ROS[C1]})(1-\exp[-0.0115 \times \text{BUI}])}<1$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B458%7D%7B1500(%5Ctext%7BROS%5BC1%5D%7D)(1-%5Cexp%5B-0.0115%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%7D%3C1">

<!-- $$
\text{M} = 225(1-\exp[-0.23(\text{ROS}-\frac{458}{450(1-\exp[-0.023(\text{FFMC}-81)])})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20225(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D-%5Cfrac%7B458%7D%7B450(1-%5Cexp%5B-0.023(%5Ctext%7BFFMC%7D-81)%5D)%7D)%5D)"></div>

Else M = 0.

#### C2

<!-- $$
\text{HFI} = \text{M} + 5(1-\exp[-0.0115 \times \text{BUI}])(\text{ROS})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20%5Ctext%7BM%7D%20%2B%205(1-%5Cexp%5B-0.0115%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)(%5Ctext%7BROS%7D)"></div>

If <!-- $\frac{842}{1500(\text{ROS})(1-\exp[-0.0115 \times \text{BUI}])}$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B842%7D%7B1500(%5Ctext%7BROS%7D)(1-%5Cexp%5B-0.0115%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%7D"> <1:

<!-- $$
\text{M} = 240(1-\exp[-0.23(\text{ROS}-\frac{842}{1500(1-\exp[-0.0115 \times \text{BUI}])})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20240(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D-%5Cfrac%7B842%7D%7B1500(1-%5Cexp%5B-0.0115%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%7D)%5D)"></div>

Else M = 0.

#### C3

<!-- $$
\text{HFI} = M + 5(1-\exp[-0.0164 \times \text{BUI}]^{2.24})(\text{ROS})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20M%20%2B%205(1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D%5E%7B2.24%7D)(%5Ctext%7BROS%7D)"></div>

If <!-- $\frac{3667}{1500(\text{ROS})(1-\exp[-0.0164 \times \text{BUI}])^{2.24}} < 1$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B3667%7D%7B1500(%5Ctext%7BROS%7D)(1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D%7D%20%3C%201">

<!-- $$
\text{M} = 300(1.15)(1-\exp[-0.23(\text{ROS} - \frac{3667}{1500(1-\exp[-0.0164 \times \text{BUI}])})^{2.24}])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20300(1.15)(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D%20-%20%5Cfrac%7B3667%7D%7B1500(1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%7D)%5E%7B2.24%7D%5D)"></div>

Else <!-- $\text{M} = 0$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%200">.

#### C3m

<!-- $$
\text{HFI} = \text{M} + 5(1 - \exp[-0.0164 \times \text{BUI}])^{2.24}(\text{ROS})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20%5Ctext%7BM%7D%20%2B%205(1%20-%20%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D(%5Ctext%7BROS%7D)"></div>

If <!-- $\frac{1296}{1500(\text{ROS})((1-\exp[-0.0164 \times \text{BUI}])^{2.24})}$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B1296%7D%7B1500(%5Ctext%7BROS%7D)((1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D)%7D"> <1:

<!-- $$
\text{M} = 345(1-\exp[-0.23(\text{ROS} - \frac{1296}{1500(1-\exp[-0.0164 \times \text{BUI}])^{2.24}})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20345(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D%20-%20%5Cfrac%7B1296%7D%7B1500(1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D%7D)%5D)"></div>

Else M = 0.

#### C4

<!-- $$
\text{HFI} = \text{M} + 5(1-\exp[-0.0164 \times \text{BUI}])^{2.24}(\text{ROS})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20%5Ctext%7BM%7D%20%2B%205(1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D(%5Ctext%7BROS%7D)"></div>

If <!-- $\frac{1296}{1500(\text{ROS})((1 - \exp[-0.0164 \times \text{BUI}])^{2.24})}$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B1296%7D%7B1500(%5Ctext%7BROS%7D)((1%20-%20%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D)%7D"> <1:

<!-- $$
\text{M} = 360(1-\exp[-0.23(\text{ROS}-\frac{1296}{1500((1-\exp[-0.0164 \times \text{BUI}])^{2.24})})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20360(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D-%5Cfrac%7B1296%7D%7B1500((1-%5Cexp%5B-0.0164%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.24%7D)%7D)%5D)"></div>

Else M = 0.

#### C5

<!-- $$
\text{HFI} = \text{M} + 5(1-\exp[-0.0149 \times \text{BUI}])^{2.48}(\text{ROS})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20%5Ctext%7BM%7D%20%2B%205(1-%5Cexp%5B-0.0149%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.48%7D(%5Ctext%7BROS%7D)"></div>

If <!-- $\frac{12375}{1500(\text{ROS})((1-\exp[-0.0149 \times \text{BUI}])^{2.48})}$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B12375%7D%7B1500(%5Ctext%7BROS%7D)((1-%5Cexp%5B-0.0149%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.48%7D)%7D"> <1:

<!-- $$
\text{M} = 345(1-\exp[-0.23(\text{ROS}-\frac{12375}{1500((1-\exp[-0.0149 \times \text{BUI}])^{2.48})})])
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%20345(1-%5Cexp%5B-0.23(%5Ctext%7BROS%7D-%5Cfrac%7B12375%7D%7B1500((1-%5Cexp%5B-0.0149%20%5Ctimes%20%5Ctext%7BBUI%7D%5D)%5E%7B2.48%7D)%7D)%5D)"></div>

Else M = 0.

#### C7

<!-- $$
\text{HFI} = 300(\text{M} \times 0.5 + \text{SFC}_{C7})
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BHFI%7D%20%3D%20300(%5Ctext%7BM%7D%20%5Ctimes%200.5%20%2B%20%5Ctext%7BSFC%7D_%7BC7%7D)"></div>

If <!-- $\frac{5124}{300 \times \text{ROS} \times \text{SFC}_{C7}}$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cfrac%7B5124%7D%7B300%20%5Ctimes%20%5Ctext%7BROS%7D%20%5Ctimes%20%5Ctext%7BSFC%7D_%7BC7%7D%7D"> <1:

<!-- $$
\text{M} = 1 - \exp[-0.23(\text{ROS}-\frac{5124}{300 \times \text{SFC}_{C7}})]
$$ --> 

<div align="center"><img src="https://render.githubusercontent.com/render/math?math=%5Ctext%7BM%7D%20%3D%201%20-%20%5Cexp%5B-0.23(%5Ctext%7BROS%7D-%5Cfrac%7B5124%7D%7B300%20%5Ctimes%20%5Ctext%7BSFC%7D_%7BC7%7D%7D)%5D"></div>

Else M = 0.

### Head Fire Intensity Groups

| HFI  | Intensity Group |
|------|-----------------|
| <500        | 1        |
| <!-- $\geq$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cgeq"> 500  | 2        |
| <!-- $\geq$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cgeq"> 1000 | 3        |
| <!-- $\geq$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cgeq"> 2000 | 4        |
| <!-- $\geq$ --> <img src="https://render.githubusercontent.com/render/math?math=%5Cgeq"> 4000 | 5        |