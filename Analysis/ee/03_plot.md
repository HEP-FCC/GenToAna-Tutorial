# Stage 3: producing the final plots

This final stage accompanies [`03_plot.py`](03_plot.py). It does not process events again: `fccanalysis plots` reads the scaled ROOT histograms produced in stage 2 and turns them into (some day) publication-style comparisons of signal and background.

## Input, output, and plot labels

The input directory must match the output directory of [`02_selection_and_hist.py`](02_selection_and_hist.py):

```python
inputDir = "outputs/stage2/"
outdir = "outputs/plots/"
```

The luminosity, collision energy, and analysis text are used to annotate the figures:

```python
intLumiLabel = "L = 10.6 ab^{-1}"
energy = 240.0
collider = "FCC-ee"
ana_tex = "e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-}b#bar{b}"
```

The histograms were already scaled in stage 2. Here, `intLumi` and `intLumiLabel` describe that normalization on the plots rather than repeating the event processing.

The remaining display options request PDF output, a linear vertical axis, stacked signal and background contributions, and statistical-uncertainty bands:

```python
formats = ["pdf"]
yaxis = ["lin"]
stacksig = ["stack"]
plotStatUnc = True
```

## Connect variables, selections, and samples

`variables` lists the histogram names to plot. They must match entries in the stage-2 `histoList`:

```python
variables = [
    "m_zmumu", "p_zmumu", "m_recoil_zmumu", "m_jj", "scoresum_B"
]
```

Similarly, the selection names must match the stage-2 `cutList`. Including every cumulative selection produces plots showing how the distributions change throughout the cut flow:

```python
selections = {
    "ZH": [
        "sel0_baseline",
        "sel1_zmass",
        "sel2_zmomentum",
        "sel3_recoil",
        "sel4_btag",
    ]
}
```

`extralabel` provides the human-readable description printed for each selection. The outer key `"ZH"` identifies this plot category and must also appear in `plots`; FCCAnalyses includes it in the output filenames.

The `plots` dictionary assigns the process names used in stage 2 to signal and background groups:

```python
plots = {
    "ZH": {
        "signal": {"ZH": ["wzp8_ee_mumuH_Hbb_ecm240"]},
        "backgrounds": {
            "ZZ": ["p8_ee_ZZ_mumubb_ecm240"],
            "WW": ["p8_ee_WW_mumu_ecm240"],
        },
    }
}
```

The group names `ZH`, `ZZ`, and `WW` connect this dictionary to the corresponding entries in `colors` and `legend`.

## Produce the plots

Run:

```bash
fccanalysis plots 03_plot.py
```

The final PDFs are written to `outputs/plots/`, separately for every requested variable and selection. Compare the progression from `sel0_baseline` to `sel4_btag`: a useful selection should preserve much of the signal while progressively reducing the backgrounds.

## Where a complete analysis would continue

This concludes the tutorial workflow, but not a complete physics analysis. A full measurement would also model every relevant signal and background component, validate the simulation in control regions, propagate experimental and theoretical systematic uncertainties, and construct a statistical likelihood.

Statistical inference could then be used to extract quantities such as a signal strength, the $ZH$ production cross section, the Higgs mass from the recoil distribution, or constraints on Higgs couplings. Those steps require careful treatment of correlations, uncertainties, and possible biases and are beyond the scope of this introductory exercise.
