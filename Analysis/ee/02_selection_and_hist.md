# Stage 2: selecting events and producing histograms

This chapter accompanies [`02_selection_and_hist.py`](02_selection_and_hist.py). Stage 1 has already reconstructed the $Z$ and jet candidates and stored the relevant observables in compact ntuples. We can therefore test tighter selections without repeating the more expensive reconstruction and flavour-tagging steps.

In this stage you will:

- choose cuts that retain the $ZH$ signal while rejecting $ZZ$ and $WW$ backgrounds;
- normalise the samples to the expected FCC-ee luminosity (10.6 ab $^{-1}$);
- produce histograms and a cut flow after each selection step.

## Choose the selection cuts

Start by comparing the signal and background distributions of the variables written in stage 1. The supplied helper script [`plot_cut_vars.py`](plot_cut_vars.py) reads the three stage-1 ntuples and creates these comparison plots for you:

```bash
python3 plot_cut_vars.py
```

It writes one PDF per variable to `outputs/plots/`:

```text
m_zmumu.pdf
p_zmumu.pdf
m_recoil_zmumu.pdf
m_jj.pdf
scoresum_B.pdf
```

Within each plot, the ZH, ZZ, and WW distributions are independently normalised to unit area.
> ✏️ **Exercise: Determine cut values**
>
> Inspect the shapes and find sensible cut values for the following variables:
>
> - `m_zmumu`: Signal events should contain a dimuon candidate compatible with the $Z$-boson mass. Choose a window that retains the peak while rejecting non-resonant and incorrectly reconstructed candidates.
> - `p_zmumu`: Two-body kinematics predict different $Z$ momenta for $ZH$ and $ZZ$ production. This provides useful discrimination between signal and background. See hint below.
> - `m_recoil_zmumu`: For signal, the system recoiling against the dimuon candidate should have a mass near $m_H$.
> - `scoresum_B`: Large values indicate two $b$-like jets. This is particularly effective against the $WW$ background, which does not normally contain two genuine $b$ jets.


> <details>
> <summary><strong>✅ Hint:</strong></summary>
>
> For a two-body process $e^+e^-\to AB$, the magnitude of either outgoing particle's momentum in the centre-of-mass frame is
>
> $p = \frac{\sqrt{\left[s-(m_A+m_B)^2\right]\left[s-(m_A-m_B)^2\right]}}{2\sqrt{s}}.$
>
> At $\sqrt{s}=240$ GeV, calculate the expected $Z$ momentum for:
>
> 1. $e^+e^-\to ZH$, using $m_A=m_Z$ and $m_B=m_H$;
> 2. $e^+e^-\to ZZ$, using $m_A=m_B=m_Z$.
>
> Compare your results with `outputs/plots/p_zmumu.pdf`. Then choose a momentum window that retains the $ZH$ peak while reducing the $ZZ$ contribution.
> </details>
<br>


Enter your chosen boundaries at the top of the script:

```python
Z_MASS_MIN = FILLME
Z_MASS_MAX = FILLME
Z_MOMENTUM_MIN = FILLME
Z_MOMENTUM_MAX = FILLME
RECOIL_MASS_MIN = FILLME
RECOIL_MASS_MAX = FILLME
BTAG_SUM_MIN = FILLME
```

These values are analysis choices, not fundamental constants. Changing them later requires rerunning only this histogram stage and the plotting stage—not stage 1.

## Normalise the samples

The selected Monte Carlo samples contain different numbers of generated events and represent processes with different production rates. To compare their expected yields, each sample is scaled according to

$$
N_{\mathrm{expected}}
= \frac{N_{\mathrm{selected}}}{N_{\mathrm{generated}}}
  \times \sigma_{\mathrm{eff}} \times k \times \epsilon_{\mathrm{match}} \times \mathcal{L}.
$$

Here, $\sigma_{\mathrm{eff}}$ is the effective cross section of the generated final state, $k$ is an optional higher-order correction, $\epsilon_{\mathrm{match}}$ is an optional generator-matching efficiency, and $\mathcal{L}$ is the integrated luminosity. For these samples, the latter two correction factors are 1.

The `fccanalysis final` step requires `procDict`, which points to a JSON metadata dictionary for the chosen production campaign containing generated event counts, cross sections, $k$-factors, and matching efficiencies. We load the standard winter-2023 IDEA dictionary and use `procDictAdd` below to supply or override this metadata for our specialised tutorial samples:

```python
procDictAdd = {
    "wzp8_ee_mumuH_Hbb_ecm240": {
        "crossSection": FILLME,
        "kfactor": 1.0,
        "matchingEfficiency": 1.0,
    },
    "p8_ee_ZZ_mumubb_ecm240": {
        "crossSection": FILLME,
        "kfactor": 1.0,
        "matchingEfficiency": 1.0,
    },
    "p8_ee_WW_mumu_ecm240": {
        "crossSection": FILLME,
        "kfactor": 1.0,
        "matchingEfficiency": 1.0,
    },
}
```

> ✏️ **Exercise: Find the effective cross sections**
>
> Search for the three underlying production processes on the [FCC Physics Events webpage](https://fcc-physics-events.web.cern.ch/fcc-ee/) or directly in the [EventProducer configuration](https://github.com/HEP-FCC/EventProducer/blob/master/config/param_FCCee.py). If the complete decay chain is not listed, start from the inclusive production cross section and multiply it by the relevant branching fractions, which can be obtained from [PDG Live](https://pdglive.lbl.gov/). **Enter the resulting effective cross sections in pb.**
>
> For the signal, the [generation step](../../Gen/ee/README.md) uses WHIZARD to generate the hard process $e^+e^-\to\mu^+\mu^-H$; Pythia8 subsequently showers, hadronizes, and forces the $H\to b\bar b$ decay. The WHIZARD output gives the cross section before a Higgs decay is selected. Therefore, for a physical yield prediction of the complete $\mu^+\mu^-b\bar b$ final state, multiply it by $\mathrm{BR}(H\to b\bar b)$. The older Pythia6-showered reference sample `wzp6_ee_mumuH_Hbb_ecm240`, listed in the [EventProducer configuration](https://github.com/HEP-FCC/EventProducer/blob/master/config/param_FCCee.py), can be used to validate your calculation.
>
> **Note**: For `p8_ee_ZZ_mumubb_ecm240`, remember that either of the two identical $Z$ bosons can provide the $\mu\mu$ or $b\bar b$ decay.


## Apply cumulative selections

`cutList` defines named selection stages. Each entry repeats all preceding requirements and adds one new cut:

```python
cutList = {
    "sel0_baseline": "previous baseline selection",
    "sel1_zmass": "above + Z-mass requirement",
    "sel2_zmomentum": "above + Z-momentum requirement",
    "sel3_recoil": "above + recoil-mass requirement",
    "sel4_btag": "above + b-tag requirement"
}
```

The selections are cumulative so that their yields can be read as a cut flow. `sel0_baseline` contains every event that reached the stage-1 ntuple, while `sel4_btag` contains events passing the complete selection.

`histoList` specifies the column, title, and binning of each histogram. FCCAnalyses creates every requested histogram separately for every entry in `cutList`. The resulting files therefore allow you to inspect how each successive requirement changes the signal and background distributions.


The JSON output provides the numerical cut flow in addition to the ROOT histograms.

## Run the selection and histogram stage

After entering your cuts and cross sections, run:

```bash
fccanalysis final 02_selection_and_hist.py
```

The output is written to `outputs/stage2/`.
