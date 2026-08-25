"""Compare stage-1 variable shapes for signal and background samples.

Run after ``01_basic_selection.py`` with:
    python3 plot_cut_vars.py

Each process is normalised to unit area.  The plots therefore compare shapes
rather than expected event yields and do not depend on the input sample sizes.
"""

from pathlib import Path

import ROOT


ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetLineWidth(2)


INPUT_DIR = Path("outputs/stage1")
OUTPUT_DIR = Path("outputs/plots")

SAMPLES = {
    "wzp8_ee_mumuH_Hbb_ecm240": {
        "label": "ZH #rightarrow #mu^{+}#mu^{-}b#bar{b}",
        "color": ROOT.kRed + 1,
        "style": 1,
    },
    "p8_ee_ZZ_mumubb_ecm240": {
        "label": "ZZ #rightarrow #mu^{+}#mu^{-}b#bar{b}",
        "color": ROOT.kGreen + 2,
        "style": 2,
    },
    "p8_ee_WW_mumu_ecm240": {
        "label": "WW #rightarrow #mu^{+}#mu^{-} + X",
        "color": ROOT.kBlue + 1,
        "style": 3,
    },
}

# variable: (axis title, number of bins, lower edge, upper edge)
VARIABLES = {
    "m_zmumu": ("m_{#mu#mu} [GeV]", 100, 0.0, 200.0),
    "p_zmumu": ("p_{#mu#mu} [GeV]", 75, 0.0, 150.0),
    "m_recoil_zmumu": ("m_{recoil} [GeV]", 100, 0.0, 200.0),
    "m_jj": ("m_{jj} [GeV]", 100, 50.0, 150.0),
    "scoresum_B": ("Sum of the two jet b-tag scores", 50, 0.0, 2.0),
}


def make_histogram(sample_name, variable, binning):
    """Read one stage-1 sample and return a unit-normalised histogram."""
    input_file = INPUT_DIR / f"{sample_name}.root"
    if not input_file.is_file():
        raise FileNotFoundError(f"Input sample not found: {input_file}")

    _, nbins, xmin, xmax = binning
    dataframe = ROOT.RDataFrame("events", str(input_file))
    model = ROOT.RDF.TH1DModel(
        f"{variable}_{sample_name}", "", nbins, xmin, xmax
    )
    histogram = dataframe.Histo1D(model, variable).GetValue().Clone()
    histogram.SetDirectory(0)

    # Normalise only over the displayed range. Underflow and overflow events
    # do not influence the comparison shown in the plot.
    integral = histogram.Integral(1, histogram.GetNbinsX())
    if integral > 0.0:
        histogram.Scale(1.0 / integral)
    else:
        print(f"Warning: no entries in the plotted range for {sample_name}: {variable}")

    sample = SAMPLES[sample_name]
    histogram.SetLineColor(sample["color"])
    histogram.SetLineStyle(sample["style"])
    histogram.SetLineWidth(3)
    histogram.SetFillStyle(0)
    return histogram


def plot_variable(variable, binning):
    """Overlay the normalised distributions of all processes."""
    histograms = {
        sample_name: make_histogram(sample_name, variable, binning)
        for sample_name in SAMPLES
    }

    canvas = ROOT.TCanvas(f"canvas_{variable}", "", 800, 700)
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.05)
    canvas.SetBottomMargin(0.13)
    canvas.SetTopMargin(0.08)
    canvas.SetTicks(1, 1)

    maximum = max(histogram.GetMaximum() for histogram in histograms.values())
    first_histogram = next(iter(histograms.values()))
    first_histogram.SetMaximum(1.30 * maximum if maximum > 0.0 else 1.0)
    first_histogram.SetMinimum(0.0)
    first_histogram.GetXaxis().SetTitle(binning[0])
    first_histogram.GetYaxis().SetTitle("Normalised events / bin")
    first_histogram.GetXaxis().SetTitleSize(0.045)
    first_histogram.GetYaxis().SetTitleSize(0.045)
    first_histogram.GetXaxis().SetLabelSize(0.040)
    first_histogram.GetYaxis().SetLabelSize(0.040)
    first_histogram.GetYaxis().SetTitleOffset(1.45)
    first_histogram.Draw("HIST")

    for histogram in list(histograms.values())[1:]:
        histogram.Draw("HIST SAME")

    legend = ROOT.TLegend(0.50, 0.68, 0.92, 0.88)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextSize(0.034)
    for sample_name, histogram in histograms.items():
        legend.AddEntry(histogram, SAMPLES[sample_name]["label"], "l")
    legend.Draw()

    label = ROOT.TLatex()
    label.SetNDC(True)
    label.SetTextFont(42)
    label.SetTextSize(0.040)
    label.DrawLatex(0.14, 0.94, "FCC-ee simulation")
    label.SetTextAlign(31)
    label.DrawLatex(0.95, 0.94, "#sqrt{s} = 240 GeV")

    canvas.RedrawAxis()
    canvas.SaveAs(str(OUTPUT_DIR / f"{variable}.pdf"))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for variable, binning in VARIABLES.items():
        plot_variable(variable, binning)
        print(f"Created {OUTPUT_DIR / f'{variable}.pdf'}")


if __name__ == "__main__":
    main()
