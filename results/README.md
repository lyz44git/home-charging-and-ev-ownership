# Result tables

The five folders below hold the aggregate tables behind the [main README](../README.md) and its figures, one folder
per section. Each entry names the sample, the comparison and the table it comes from; a few sample-design and coverage
notes are given in the text only. All counts and rates are aggregates; no household records are included. The
[methods](../docs/methods.md) give the assumptions and calculations.

## 1. Data: the linked household table against the census survey ([`1_data/`](1_data/))

- **Size** ([`table_size.csv`](1_data/table_size.csv)). 348,903,764 vehicle registration rows become 53,069,701 households in 3,144 counties;
  568,210 households own a plug-in.
- **Two SQL engines** ([`sql_engine_agreement.csv`](1_data/sql_engine_agreement.csv)). The county-by-tenure aggregation gives the same result in DuckDB
  and Spark SQL in all 94,110 cells (9,411 rows, 10 measures).
- **States** ([`states_vs_acs.csv`](1_data/states_vs_acs.csv)). Against the 2025 ACS (table B25147), the correlation of state plug-in shares is
  0.24 across all states and 0.90 in the 15 states with recent vehicle records (CO, TX, TN, IA, ID, VA, WI, WY, MA, MD,
  ND, SD, NM, NC, MT; 20.8 million households). Every analysis below uses these 15 states.
- **Calibration** ([`county_error_by_method.csv`](1_data/county_error_by_method.csv)). The household table gives 2.24% of households with a plug-in,
  against 4.80% in the ACS. Error against the ACS in 259 counties, each state predicted by a model fitted on the
  other 14:

  | Method | County mean absolute error (pp) | Bias (pp) | Share within the ACS 90% margin |
  |---|---|---|---|
  | Table as built | 2.36 | −2.34 | 27% |
  | Scaled to the state total | 1.09 | −0.14 | 68% |
  | Calibrated (model and state total) | **0.95** | −0.04 | 75% |
  | *Median ACS 90% margin of error* | *1.27* | | |

  The calibrated model also gives estimates for 873 counties that the ACS 1-year tables do not publish.

## 2. Parking measured from street-level images ([`2_parking/`](2_parking/))

- **Sample.** 10,060 homes in 119 strata, with plug-in households over-sampled to 30% and inclusion probabilities
  kept. 8,491 homes (84%) have a street-level image.
- **Two models** ([`two_model_agreement.csv`](2_parking/two_model_agreement.csv)). A vision model can judge parking in 63% of images. Where a second model
  can also judge, the two agree on private parking in 98.8% of 5,021 images ([Cohen's kappa](https://doi.org/10.1177/001316446002000104) 0.96).
- **Blind audit** ([`audit_vs_model.csv`](2_parking/audit_vs_model.csv)). A reviewer labelled 600 randomly selected images without seeing the model's
  labels. Human and model could both judge 345 images and agreed on private parking in 99.7% of them. To reproduce
  this from the table (rows are the reviewer, columns the model), drop either rater's "cannot tell", count carports,
  driveways and garages as private parking, and count shared lots and no visible parking as the other category.
- **Share of homes without private off-street parking** ([`parking_shares.csv`](2_parking/parking_shares.csv)), weighted to the 15-state population:

  | Homes | Model labels only | Hand audit only | **[Prediction-powered](https://doi.org/10.1126/science.adi6000)** |
  |---|---|---|---|
  | All | 10.5% (9.5–11.4) | 10.5% (7.4–13.9) | **11.5% (9.5–13.7)** |
  | Single-family | 6.1% | 6.5% (3.6–9.8) | **7.6% (5.7–9.9)** |
  | Condo | 50.5% | 48.6% (31.7–63.7) | **52.6% (40.4–62.1)** |
  | Other multi-unit | 60.2% | 49.5% (33.8–65.0) | **57.2% (45.6–69.0)** |

  The prediction-powered interval for all homes is 36% narrower than the audit alone.
- **Property record against image** ([`parking_by_garage_record.csv`](2_parking/parking_by_garage_record.csv), [`record_vs_image_auc.csv`](2_parking/record_vs_image_auc.csv)). Single-family homes
  without private parking in the image: 1.9% where the record shows an attached garage, 3.0% with another parking
  code, 8.8% with a detached garage, 12.3% where the garage field is blank. The record's garage and parking fields
  predict the image's answer with an AUC of 0.69 for single-family homes, 0.68 for condos and 0.57 for other
  multi-unit homes.
- **Owners and renters** ([`parking_by_tenure.csv`](2_parking/parking_by_tenure.csv)). Share without private off-street parking, with 95% bootstrap
  intervals:

  | Building | Owned | Rented |
  |---|---|---|
  | Single-family | 5.6% (4.7–6.6), 3,227 homes | 6.5% (2.8–10.8), 175 homes |
  | Condo | 46.7% (41.0–52.3), 506 | 60.3% (43.3–76.7), 45 |
  | Other multi-unit | 42.1% (32.3–52.0), 180 | 79.2% (72.5–85.5), 188 |

  Single-family, renter minus owner: 0.9 points (−2.9 to 5.3).
- **Ownership among homes with visible parking** ([`ownership_odds_image_sample.csv`](2_parking/ownership_odds_image_sample.csv)). Renters against owners, with
  household controls: odds ratio 0.39 (0.24–0.65) for single-family homes (162 rented homes) and 0.37 (0.23–0.57) for
  all building types.
- **Image model** ([`image_model_scores.csv`](2_parking/image_model_scores.csv)). A [ConvNeXt-Tiny](https://doi.org/10.1109/CVPR52688.2022.01167) trained on the vision model's labels in 12 states scores
  0.922 AUC against those labels (1,485 images) and 0.946 against the hand labels (105 images) in three states it
  never saw.

## 3. Renters against comparable owners ([`3_renter_gap/`](3_renter_gap/))

878,879 renter households and a 12% random sample of owner households (1,660,856 sampled, representing 13.8 million)
of single-family homes in the 15 states.

- **Ownership by vehicle** ([`ownership_renters_vs_owners.csv`](3_renter_gap/ownership_renters_vs_owners.csv)):

  | Vehicle | Renters | All owners | Comparable owners (AIPW) | Unadjusted ratio | [IPW](https://doi.org/10.1111/1468-0262.00442) ratio | [AIPW](https://doi.org/10.1080/01621459.1994.10476818) ratio | [DML](https://doi.org/10.1111/ectj.12097), points |
  |---|---|---|---|---|---|---|---|
  | Plug-in | 0.91% | 2.76% | 1.75% | 0.33 | 0.50 (0.48–0.51) | **0.52 (0.50–0.54)** | −0.86 (−0.90 to −0.82) |
  | Battery-electric | 0.66% | 2.14% | 1.36% | 0.31 | 0.46 (0.44–0.48) | 0.49 (0.47–0.51) | −0.71 (−0.74 to −0.67) |
  | Hybrid | 2.54% | 5.36% | 3.91% | 0.48 | 0.63 (0.62–0.65) | 0.65 (0.64–0.66) | −1.44 (−1.50 to −1.38) |
  | Recent luxury gasoline | 4.87% | 11.36% | 6.73% | 0.43 | 0.69 (0.68–0.71) | 0.72 (0.71–0.74) | −1.84 (−1.92 to −1.76) |

- **Net gap** ([`net_gap_by_estimator.csv`](3_renter_gap/net_gap_by_estimator.csv), [`exact_matching.csv`](3_renter_gap/exact_matching.csv), [`poisson_by_household_type.csv`](3_renter_gap/poisson_by_household_type.csv)): the plug-in ratio
  divided by the comparison vehicle's ratio, minus one.

  | Estimator | Against hybrids | Against recent luxury gasoline |
  |---|---|---|
  | Unadjusted | −30.6% (−32.5 to −28.7) | −23.1% (−25.0 to −21.1) |
  | IPW | −21.6% (−24.7 to −18.4) | −28.2% (−31.1 to −25.2) |
  | **AIPW** | **−20.1% (−23.4 to −16.7)** | **−28.3% (−31.3 to −25.1)** |
  | Exact matching | −29.2% (−31.7 to −26.6) | −31.9% (−34.1 to −29.3) |
  | Poisson with ZIP code fixed effects | −29% (−31 to −27) | −31% (−33 to −29) |

- **Vehicle types** ([`gap_by_vehicle_type.csv`](3_renter_gap/gap_by_vehicle_type.csv)), AIPW, renters against comparable owners:

  | Vehicle | Renters | Comparable owners | Difference |
  |---|---|---|---|
  | Recent luxury gasoline | 4.87% | 6.73% | −27.7% (−29.1 to −26.2) |
  | Hybrid | 2.54% | 3.91% | −35.1% (−36.5 to −33.6) |
  | Plug-in hybrid | 0.26% | 0.42% | −37.2% (−41.3 to −32.9) |
  | Battery-electric | 0.66% | 1.36% | −51.4% (−53.5 to −49.3) |

  Adjacent types as ratios of ratios: plug-in hybrid against hybrid −3.4% (−9.9 to 3.7); battery-electric against
  plug-in hybrid −22.6% (−28.4 to −16.3).

- **Exact matching** ([`exact_matching.csv`](3_renter_gap/exact_matching.csv), [`exact_matching_by_vehicle.csv`](3_renter_gap/exact_matching_by_vehicle.csv),
  [`exact_matching_two_or_more_vehicles.csv`](3_renter_gap/exact_matching_two_or_more_vehicles.csv)). Each renter is compared with owners in the same cell; 95% intervals
  from 500 bootstrap draws of ZIP codes.

  | Cell | Renters matched | Plug-in | Hybrid | Luxury gasoline | Net gap against hybrids | Against luxury gasoline |
  |---|---|---|---|---|---|---|
  | ZIP code, wealth decile, age band | 866,056 (98.5%) | −56.8% | −40.0% | −37.6% | −28.0% (−30.0 to −25.7) | −30.8% (−32.7 to −28.5) |
  | + household size, years at the address | 692,029 (78.7%) | −58.5% | −41.3% | −39.0% | −29.2% (−31.7 to −26.6) | −31.9% (−34.1 to −29.3) |
  | + construction era, education | 270,089 (30.7%) | −55.2% | −38.0% | −32.2% | −27.8% (−31.3 to −23.9) | −34.0% (−36.9 to −30.2) |

  By vehicle type, second cell: plug-in hybrid −47.1% (−50.0 to −44.1), battery-electric −61.9% (−63.3 to −60.5);
  battery-electric against plug-in hybrid −28.0% (−32.4 to −23.1). Households with two or more vehicles (634,839
  renter households, 76.3% matched): net gap −26.2% (−29.0 to −23.3) against hybrids and −30.3% (−32.6 to −27.8)
  against luxury gasoline; battery-electric against plug-in hybrid −27.9% (−32.2 to −23.4).

- **Household types** ([`poisson_by_household_type.csv`](3_renter_gap/poisson_by_household_type.csv)). [Poisson regression](https://doi.org/10.1162/rest.88.4.641) with ZIP code fixed effects on 15.8
  million households, relative to single-family owners in the same ZIP code with the same wealth decile, age,
  education and household size:

  | Household | Plug-in | Luxury gasoline | Hybrid | Net gap against luxury gasoline | Against hybrids |
  |---|---|---|---|---|---|
  | Single-family renters (879k) | −55% | −35% | −37% | −31% (−33 to −29) | −29% (−31 to −27) |
  | Condo owners (518k) | −17% | +8% | +8% | −23% (−26 to −21) | −23% (−26 to −20) |
  | Condo renters (68k) | −62% | −27% | −27% | −48% (−51 to −44) | −47% (−51 to −44) |
  | Apartment renters (275k) | −67% | −46% | −34% | −39% (−42 to −35) | −50% (−53 to −47) |
  | Duplex owners (101k) | −31% | −19% | −14% | −14% (−19 to −8) | −19% (−24 to −14) |

- **Households at the address for 15 years or more** ([`gap_by_group.csv`](5_which_renters/gap_by_group.csv), [`poisson_by_household_type.csv`](3_renter_gap/poisson_by_household_type.csv)). For
  single-family renters, AIPW gives net gaps of −8.6% (−14.4 to −2.3) against hybrids and −9.9% (−15.4 to −4.0)
  against recent luxury gasoline cars; the Poisson estimates are −19.3% (−26.3 to −11.6) and −16.7% (−24.0 to −8.7).
  For condo owners, the Poisson estimates are −27.4% (−31.8 to −22.8) and −30.3% (−34.6 to −25.6).

- **Balance and overlap** ([`balance.csv`](3_renter_gap/balance.csv), [`overlap.csv`](3_renter_gap/overlap.csv)). The largest standardized difference between renters and
  owners is 0.60 before weighting (household size) and 0.04 after; none of 43 covariates exceeds 0.1 after weighting.
  The propensity model has an AUC of 0.86; the median probability of renting is 0.17 among renters and 0.02 among
  owners; 31% of owners and 2% of renters fall outside 0.01–0.99; the weighted owners carry an effective sample of
  212,693 households.

- **Sensitivity** ([`sensitivity.csv`](3_renter_gap/sensitivity.csv), [`net_gap_controls_omitted.csv`](3_renter_gap/net_gap_controls_omitted.csv)). [E-value](https://doi.org/10.7326/M16-2607) 1.81 for the net ratio against hybrids
  (1.69 at the interval bound) and 2.13 against luxury gasoline cars (2.00). [Robustness value](https://doi.org/10.1111/rssb.12348) of the DML estimate for
  plug-ins: 2.5%. Controls omitted, on a 3% sample of owners with three-fold cross-fitting (AIPW):

  | Specification | Plug-in ratio | Net gap against hybrids | Against luxury gasoline |
  |---|---|---|---|
  | Full controls, this sample | 0.51 | −24.8% (−31.6 to −17.3) | −28.4% (−36.8 to −18.9) |
  | No controls for wealth and home value | 0.50 | −23.1% (−31.3 to −13.8) | −28.4% (−36.7 to −18.9) |
  | No controls for the ZIP code and state | 0.55 | −18.6% (−24.3 to −12.6) | −24.8% (−30.6 to −18.6) |
  | No control for years at the address | 0.55 | −22.6% (−30.3 to −13.9) | −25.3% (−32.8 to −16.9) |
  | Tenure not recorded counted as renting | 0.62 | −17.3% (−22.7 to −11.5) | −20.9% (−25.8 to −15.6) |

## 4. Policy simulation ([`4_policy/`](4_policy/))

- **Size of the barrier** ([`barrier_size.csv`](4_policy/barrier_size.csv)). Among 878,879 renter households, 7,999 own a plug-in. At the
  ownership rate of comparable owners, 15,412 would own one, a shortfall of 7,413 households. Removing the net gap adds
  2,011 plug-in households using hybrids as the comparison (25% more; 1,600 to 2,441) and 3,151 using recent luxury
  gasoline cars (39% more; 2,681 to 3,643). In the file, "ci low" and "ci high" refer to bounds on the net ratio; a
  lower ratio implies more additional households.
- **The barrier in dollars** ([`barrier_size.csv`](4_policy/barrier_size.csv), [`price_equivalent.csv`](4_policy/price_equivalent.csv)). Median price of plug-in vehicles owned in
  the 15 states: $48,490. Price equivalent per vehicle: $4,105 and $5,465 against hybrids (elasticities −2.76 from
  [Xing, Leard and Li 2021](https://doi.org/10.1016/j.jeem.2021.102432) and −2.1 from
  [Muehlegger and Rapson 2022](https://doi.org/10.1016/j.jpubeco.2022.104752)); $6,201 and $8,309 against luxury
  gasoline cars; 55% to 111% of the former $7,500 federal tax credit.
- **Installation cost** ([`permit_costs.csv`](4_policy/permit_costs.csv)), declared values in public electrical permits:

  | Permits | Number | Median | 25th–75th percentile |
  |---|---|---|---|
  | Cambridge, MA, charger only | 131 | $1,500 | $1,084–$2,500 |
  | Cambridge, MA, charger with panel or service work | 39 | $4,350 | $2,250–$7,890 |
  | Dallas, TX, charger only, value of $100 or more | 39 | $645 | $495–$1,291 |

- **Two policies** ([`policy_costs.csv`](4_policy/policy_costs.csv), [`simulation_checks.csv`](4_policy/simulation_checks.csv)). Household-level simulation of 878,879 renter
  households, 500 draws. In both files, "plug-ins added" and "cost per additional plug-in" count households owning a
  plug-in. The rebate amount is per eligible vehicle, and the 76% below is the share of rebate recipients who would own
  a plug-in without it.

  | Policy | Plug-in households added | Spending | Cost per additional household (95% range) | Draws in which it costs less than the rebate |
  |---|---|---|---|---|
  | Purchase rebate | 2,595 | $64.0M | $24,440 (20,497–29,158) | |
  | Installation support, only new plug-in households claim, full barrier removed | 2,595 | $7.1M | $2,728 (2,617–2,831) | 100% |
  | Installation support, all plug-in renters claim, full barrier removed | 2,595 | $28.9M | $11,638 (8,833–15,607) | 100% |
  | Installation support, all plug-in renters claim, half the barrier removed | 1,297 | $25.3M | $20,565 (14,908–28,692) | 71% |
  | Installation support, all plug-in renters claim, a quarter removed | 648 | $23.5M | $38,422 (26,985–55,994) | 3% |

  76% of rebate recipients would own a plug-in without the rebate. The mean rebate is $5,967 per vehicle.

## 5. Which renters, and other states ([`5_which_renters/`](5_which_renters/))

- **By group** ([`gap_by_group.csv`](5_which_renters/gap_by_group.csv)). Net gap of renters, doubly robust group estimates:

  | Group | Against hybrids | Against recent luxury gasoline |
  |---|---|---|
  | Under 45 | −21.0% (−25.7 to −15.9) | −31.5% (−35.3 to −27.6) |
  | 45 to 64 | −18.5% (−22.4 to −14.3) | −28.5% (−31.5 to −25.3) |
  | 65 and over | −6.8% (−11.8 to −1.5) | −15.8% (−20.1 to −11.2) |
  | At the address under 5 years | −9.7% (−14.9 to −4.3) | −26.0% (−29.8 to −22.0) |
  | 5 to 14 years | −20.5% (−23.9 to −17.0) | −32.0% (−34.7 to −29.3) |
  | 15 years or more | −8.6% (−14.4 to −2.3) | −9.9% (−15.4 to −4.0) |
  | Home built before 1960 | −25.5% (−32.0 to −18.5) | −30.4% (−36.3 to −24.0) |
  | 1960 to 1999 | −19.4% (−23.5 to −15.1) | −24.6% (−28.2 to −20.8) |
  | 2000 or later | −11.2% (−15.2 to −7.1) | −25.3% (−28.2 to −22.3) |
  | Wealth, lowest third | −19.6% (−26.6 to −12.0) | −25.3% (−31.6 to −18.3) |
  | Middle third | −9.0% (−15.3 to −2.2) | −20.4% (−25.6 to −14.8) |
  | Highest third | −17.6% (−20.7 to −14.3) | −25.9% (−28.4 to −23.3) |

- **[Causal forest](https://doi.org/10.1080/01621459.2017.1319839)** ([`forest_fifths.csv`](5_which_renters/forest_fifths.csv)), fitted on 250,000 households and evaluated on 600,000 others:

  | Fifth by predicted effect | Predicted, points | Doubly robust estimate, points | Plug-in rate if owning | Ratio |
  |---|---|---|---|---|
  | 1 (largest) | −2.92 | −2.65 | 6.86% | 0.61 (0.56–0.68) |
  | 2 | −1.35 | −0.91 | 2.42% | 0.62 (0.53–0.74) |
  | 3 | −0.70 | −0.61 | 1.23% | 0.50 (0.39–0.65) |
  | 4 | −0.35 | −0.24 | 0.64% | 0.62 (0.44–0.88) |
  | 5 (smallest) | −0.16 | −0.20 | 0.36% | 0.44 (0.26–0.72) |

- **Where the shortfall is** ([`shortfall_share_by_ranking.csv`](5_which_renters/shortfall_share_by_ranking.csv), [`ranking_overlap.csv`](5_which_renters/ranking_overlap.csv)). Share of the estimated
  ownership shortfall among 300,000 scored renters, with 95% bootstrap intervals:

  | Ranking | Top 20% of renters | Top 40% |
  |---|---|---|
  | Ownership model | 60.1% (58.2–61.9) | 80.3% (79.1–81.6) |
  | Causal forest | 59.9% (57.9–61.8) | 82.0% (80.7–83.7) |
  | Random | 20% | 40% |

  The two rankings have a rank correlation of 0.87, and 79% of the top fifth of one is in the top fifth of the other.

- **Other states** ([`auc_by_held_out_state.csv`](5_which_renters/auc_by_held_out_state.csv)). Each of the 15 states is predicted by an ownership model trained on
  the other 14. With people, home and place features the AUC is between 0.72 and 0.81 in every state. Predicted
  totals run from 0.73 of the actual count (Colorado) to 2.93 times (North Dakota).

- **Vehicle history** ([`vehicle_history_models.csv`](5_which_renters/vehicle_history_models.csv)). Is the household's newest vehicle a plug-in? Trained on 3.1
  million households in 12 states, tested on 0.97 million in three others:

  | Model | AUC | Average precision |
  |---|---|---|
  | Household and home only | 0.849 | 0.142 |
  | [Gradient boosting](https://doi.org/10.1214/aos/1013203451) with summaries of older vehicles | 0.870 | 0.213 |
  | [GRU](https://doi.org/10.3115/v1/D14-1179) over the vehicle sequence | 0.871 | 0.217 |
  | [Transformer](https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) over the vehicle sequence | 0.870 | 0.213 |
