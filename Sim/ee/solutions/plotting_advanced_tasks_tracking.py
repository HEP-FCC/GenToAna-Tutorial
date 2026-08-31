import ROOT
import os
import numpy as np

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)  # disable the stats box, it overlaps the legend

ROOT.gInterpreter.Declare('#include "edm4hep/TrackState.h"')
ROOT.gInterpreter.Declare('#include "edm4hep/Track.h"')

ROOT.gInterpreter.Declare("""
using namespace edm4hep;

float get_track_eta(const TrackState& state) {
    return std::asinh(state.tanLambda);
}

float get_track_d0(const TrackState& state) {
    return state.D0;
}

float get_track_pt(const TrackState& state, float fB) {
    float C = -0.5 * 1e3 * state.omega;
    return fB * 0.2998 / std::abs(2 * C);
}

float get_track_pt_res(const TrackState& state) {
    float sigma_omega = std::sqrt(state.getCovMatrix(edm4hep::TrackParams::omega, edm4hep::TrackParams::omega));
    return sigma_omega / std::abs(state.omega);  // = sigma_pT / pT
}

ROOT::VecOps::RVec<float> get_track_etas(const ROOT::VecOps::RVec<TrackState>& states) {
    ROOT::VecOps::RVec<float> result;
    for (const auto& s : states) result.push_back(get_track_eta(s));
    return result;
}

ROOT::VecOps::RVec<float> get_track_d0s(const ROOT::VecOps::RVec<TrackState>& states) {
    ROOT::VecOps::RVec<float> result;
    for (const auto& s : states) result.push_back(get_track_d0(s));
    return result;
}

ROOT::VecOps::RVec<float> get_track_pts(const ROOT::VecOps::RVec<TrackState>& states, float fB) {
    ROOT::VecOps::RVec<float> result;
    for (const auto& s : states) result.push_back(get_track_pt(s, fB));
    return result;
}

ROOT::VecOps::RVec<float> get_track_pt_ress(const ROOT::VecOps::RVec<TrackState>& states) {
    ROOT::VecOps::RVec<float> result;
    for (const auto& s : states) result.push_back(get_track_pt_res(s));
    return result;
}

""")

# Define input/output - EDIT HERE:
# "baseline" is the reference every other variant is compared against.
# Each non-baseline entry gets its own pairwise plot vs. baseline -- variants
# are never plotted against each other.
variants = {
    "baseline": "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/wzp8_ee_mumuH_Hbb_ecm240.edm4hep.root",
    "removedInnerVTXLayer": "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/mumuH_delphes_IDEA_removedInnerVTXLayer.edm4hep.root",
    "nMinHits25": "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/mumuH_delphes_IDEA_nTrackHits25.edm4hep.root",
    "BField05": "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/mumuH_delphes_IDEA_B05.edm4hep.root",
}

out_dir = "./plots"
color_baseline = ROOT.kBlue+2
color_variant = ROOT.kRed+2

os.makedirs(out_dir, exist_ok=True)


def get_histograms(input_file):
    df = ROOT.RDataFrame("events", input_file)

    # Read the actual field used for this file's reconstruction to correctly calculate momenta: 
    bz_values = df.Take["ROOT::VecOps::RVec<float>"]("magFieldBz").GetValue()
    Bz = bz_values[0][0]
    print(f"Info: using Bz = {Bz} T for {input_file}")

    df = (df
        .Define("track_eta", "get_track_etas(_EFlowTrack_trackStates)")
        .Define("track_D0", "get_track_d0s(_EFlowTrack_trackStates)")
        .Define("track_pt", f"get_track_pts(_EFlowTrack_trackStates, {Bz}f)")
        .Define("track_pt_res", f"get_track_pt_ress(_EFlowTrack_trackStates)")
    )

    # Define histograms
    hist_eta = df.Histo1D(("hist_eta", "Track #eta;#eta;Normalized entries (a.u.)", 60, -3.0, 3.0), "track_eta")

    # D0 histogram, zoomed in to the resolution-relevant range (+/- 50 microns)
    hist_d0 = df.Histo1D(("hist_d0", "Track d_{0};d_{0} [mm];Normalized entries (a.u.)", 200, -0.05, 0.05), "track_D0")

    # pT histogram with logarithmic binning
    n_bins_pt = 50
    pt_min, pt_max = 0.1, 100.0
    bin_edges = np.logspace(np.log10(pt_min), np.log10(pt_max), n_bins_pt + 1)
    hist_pt = df.Histo1D(
        ("hist_pt", "Track p_{T};p_{T} [GeV];Normalized entries (a.u.)", n_bins_pt, bin_edges),
        "track_pt"
    )

    # track resolution 
    hist_ptres = df.Histo1D(("hist_ptres", "Track p_{T} resolution;#sigma_{p_{T}}/p_{T};Normalized entries (a.u.)", 60, 0.0, 0.02), "track_pt_res")

    return {"eta": hist_eta, "d0": hist_d0, "pt": hist_pt, "pt_res":hist_ptres}




# Build histograms for every variant first, keeping them all in memory
all_hists = {prefix: get_histograms(f) for prefix, f in variants.items()}
baseline_hists = all_hists["baseline"]


def make_pairwise_plot(variable, logscale, variant_prefix, variant_hists):
    c = ROOT.TCanvas(f"c_{variable}_{variant_prefix}", "c", 800, 700)

    pad_top = ROOT.TPad("pad_top", "top", 0, 0.3, 1, 1.0)
    pad_top.SetBottomMargin(0.02)
    pad_top.SetLogx(logscale)
    pad_top.SetLogy(logscale)
    pad_top.Draw()

    pad_bot = ROOT.TPad("pad_bot", "bottom", 0, 0.0, 1, 0.3)
    pad_bot.SetTopMargin(0.02)
    pad_bot.SetBottomMargin(0.35)
    pad_bot.SetLogx(logscale)
    pad_bot.Draw()

    # --- Top pad: normalized baseline vs. this one variant ---
    pad_top.cd()
    legend = ROOT.TLegend(0.6, 0.65, 0.88, 0.88)
    legend.SetMargin(0.1)  

    h_base = baseline_hists[variable].GetValue().Clone(f"{variable}_baseline_{variant_prefix}")
    h_base.SetDirectory(0)
    h_base.Scale(1.0 / h_base.Integral())
    h_base.SetLineColor(color_baseline)
    h_base.SetLineWidth(2)
    h_base.GetXaxis().SetLabelSize(0)
    h_base.GetXaxis().SetTitleSize(0)
    h_base.Draw("HIST")
    legend.AddEntry(h_base, "baseline", "l")
    legend.SetFillStyle(0)   
    legend.SetLineWidth(0) 

    h_var = variant_hists[variable].GetValue().Clone(f"{variable}_{variant_prefix}")
    h_var.SetDirectory(0)
    h_var.Scale(1.0 / h_var.Integral())
    h_var.SetLineColor(color_variant)
    h_var.SetLineWidth(2)
    h_var.Draw("HIST SAME")
    legend.AddEntry(h_var, variant_prefix, "l")

    legend.Draw()

    # --- Bottom pad: ratio of this variant to baseline ---
    pad_bot.cd()
    h_ratio = h_var.Clone(f"ratio_{variable}_{variant_prefix}")
    h_ratio.SetDirectory(0)
    h_ratio.Divide(h_base)
    h_ratio.SetLineColor(color_variant)
    h_ratio.SetLineWidth(2)
    h_ratio.SetTitle("")
    h_ratio.GetYaxis().SetTitle("variant / baseline")
    h_ratio.GetYaxis().SetNdivisions(505)
    h_ratio.GetYaxis().SetTitleSize(0.11)
    h_ratio.GetYaxis().SetLabelSize(0.09)
    h_ratio.GetYaxis().SetTitleOffset(0.4)
    h_ratio.GetXaxis().SetTitleSize(0.11)
    h_ratio.GetXaxis().SetLabelSize(0.09)
    h_ratio.SetMinimum(0.0)
    h_ratio.SetMaximum(2.0)
    h_ratio.Draw("HIST")

    line = ROOT.TLine(h_ratio.GetXaxis().GetXmin(), 1.0, h_ratio.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.Draw()

    c.SaveAs(f"{out_dir}/{variant_prefix}_vs_baseline_{variable}.png")


# One pairwise plot (baseline vs. variant) per non-baseline entry per variable we look at
print(f"Plotting comparisons to: {out_dir}")

for variant_prefix, variant_hists in all_hists.items():
    if variant_prefix == "baseline":
        continue
    for variable, logscale in [("eta", False), ("d0", False), ("pt", True), ("pt_res", False)]:
        make_pairwise_plot(variable, logscale, variant_prefix, variant_hists)

print("Done with plotting.")