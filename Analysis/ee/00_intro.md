# Introduction to the FCCAnalyses tutorial

In this tutorial, you will build a small staged analysis targeting

```math
e^+e^- \rightarrow ZH \rightarrow \mu^+\mu^-b\bar b
```

at a centre-of-mass energy of $240$ GeV. The signal is compared with dominant $ZZ$ and $WW$ backgrounds. Starting from reconstructed simulated events, you will build physics candidates, reduce the input to a compact ntuple, choose event selections, normalise the samples, and produce final plots. While this will not be enough to get your name on a paper — the tutorial does not cover important aspects such as statistical modelling, inference, or the estimation of systematic uncertainties — it should give you a useful first impression of some of the capabilities provided by FCCAnalyses.

## Where FCCAnalyses fits in the software stack

[Key4hep](https://key4hep.github.io/key4hep-doc/main/getting_started/introduction.html) is the common software stack for future-collider studies. It provides compatible versions of packages used across the event-processing chain, including ROOT, EDM4hep, podio, DD4hep, and FCCAnalyses. A centrally built stack is distributed through CVMFS, so the environment can usually be prepared with:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh
```

This makes the `fccanalysis` command and its required libraries available without compiling them individually.


### EDM4hep input data

[EDM4hep](https://edm4hep.web.cern.ch/) defines the common event data model used to represent objects such as Monte Carlo particles, reconstructed particles, tracks, vertices, and calorimeter hits, together with the relations between them. It is implemented using podio and can be stored in ROOT files.

The samples used in this tutorial have already passed through event generation, detector simulation, and reconstruction. FCCAnalyses starts from the resulting EDM4hep ROOT files.

### FCCAnalyses and RDataFrame

[FCCAnalyses](https://hep-fcc.github.io/FCCAnalyses/) is an analysis framework built around ROOT's [`RDataFrame`](https://root.cern/doc/master/classROOT_1_1RDataFrame.html). An analysis constructs a computation graph using operations such as:

- `Define()` to create a new column;
- `Filter()` to select events;
- `Snapshot()` or the FCCAnalyses output mechanism to write a reduced ntuple;
- histogram actions to aggregate event-level quantities.

RDataFrame evaluates this graph lazily: defining a column or filter describes the work, while an output action triggers the event loop. This lets ROOT optimise the execution and, when enabled, process events in parallel.

The analysis is configured in Python, while many operations are implemented in compiled C++ for performance. FCCAnalyses provides reusable C++ analyzers for EDM4hep objects, and analysts can add custom helpers that ROOT compiles just in time.

## Tutorial workflow

The analysis is divided into three stages so that expensive reconstruction does not need to be repeated whenever a cut or plot style changes.

### 1. Build candidates and write a flat ntuple

[`01_basic_selection.md`](01_basic_selection.md) accompanies [`01_basic_selection.py`](01_basic_selection.py). You will retrieve reconstructed muons, build a $Z\to\mu^+\mu^-$ candidate, calculate the recoil mass, cluster the rest of the event into two jets, run flavour tagging, and write the relevant observables to a compact ROOT ntuple.

```bash
fccanalysis run 01_basic_selection.py
```

### 2. Choose selections and produce histograms

[`02_selection_and_hist.md`](02_selection_and_hist.md) first uses [`plot_cut_vars.py`](plot_cut_vars.py) to compare unit-normalised signal and background shapes. You will then choose cumulative cuts, supply the sample normalisation metadata, and produce scaled histograms and cut-flow information.

```bash
python3 plot_cut_vars.py
fccanalysis final 02_selection_and_hist.py
```

### 3. Produce the final plots

[`03_plot.md`](03_plot.md) explains how [`03_plot.py`](03_plot.py) uses the scaled histograms produced in the previous stage to create the final plots.

```bash
fccanalysis plots 03_plot.py
```

Completed versions of the exercises are available in `solutions/`, but try to work through the questions before consulting them.

## Scope of the exercise

This tutorial demonstrates the technical path from reconstructed EDM4hep events to plotting event candidate distributions for our signal decay. A complete measurement would go further: it would include all relevant background processes, validate the modelling, estimate experimental and theoretical systematic uncertainties, construct a statistical model, and perform inference to extract physical parameters.