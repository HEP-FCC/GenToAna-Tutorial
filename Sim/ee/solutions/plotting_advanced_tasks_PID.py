import ROOT
import os
import numpy as np

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)  # disable the stats box, it overlaps the legend

ROOT.gInterpreter.Declare('#include "edm4hep/TrackState.h"')
ROOT.gInterpreter.Declare('#include "edm4hep/RecDqdx.h"')
ROOT.gInterpreter.Declare('#include "edm4hep/Track.h"')
ROOT.gInterpreter.Declare('#include "edm4hep/TrackerHit3D.h"')

ROOT.gInterpreter.Declare("""
using namespace edm4hep;

float get_track_mom(const TrackState& state) {
    double fB = 2.0; // Tesla
    float C = -0.5 * 1e3 * state.omega;
    float phi0 = state.phi;
    float ct = state.tanLambda;
    float pt = fB * 0.2998 / std::abs(2 * C);
    TVector3 p(pt * std::cos(phi0), pt * std::sin(phi0), pt * ct);
    return p.Mag();
}

float get_dndx_value(const RecDqdxData& rec) {
    return rec.dQdx.value;
}

ROOT::VecOps::RVec<float> get_dndx_values(const ROOT::VecOps::RVec<RecDqdxData>& recs) {
    ROOT::VecOps::RVec<float> result;
    for (const auto& r : recs) result.push_back(get_dndx_value(r));
    return result;
}

float get_track_mtof(const TrackState& state, float L, float t_last) {
    const float c = 2.99792458e8; // m/s
    float p = get_track_mom(state);
    float L_m = L * 0.001; // mm -> m
    float beta = L_m / (c * t_last);
    float arg = 1.0/(beta*beta) - 1.0;
    if (arg < 0) return -1.0; // timing noise pushed beta >= 1; unphysical, flag it
    return p * std::sqrt(arg);
}

ROOT::VecOps::RVec<float> get_track_mtofs(const ROOT::VecOps::RVec<TrackState>& states,
                                           const ROOT::VecOps::RVec<float>& lengths,
                                           const ROOT::VecOps::RVec<unsigned int>& trackerHits_end,
                                           const ROOT::VecOps::RVec<int>& hit_rel_index,
                                           const ROOT::VecOps::RVec<float>& hit_times) {
    ROOT::VecOps::RVec<float> result;
    for (size_t i = 0; i < states.size(); ++i) {
        unsigned int last_local = trackerHits_end[i] - 1;
        int global_idx = hit_rel_index[last_local];
        float t_last = hit_times[global_idx];
        float m = get_track_mtof(states[i], lengths[i], t_last);
        if (m >= 0) result.push_back(m); // drop unphysical entries rather than plotting -1
    }
    return result;
}
""")

# Define input/output - EDIT HERE:
# "baseline" is the reference every other variant is compared against.
variants = {
    "baseline": "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/wzp8_ee_mumuH_Hbb_ecm240.edm4hep.root",
    "PID_changes": "/eos/experiment/fcc/hh/tutorials/temp/mumuH_delphes_IDEA_Gas3_TimeSmear100ps.edm4hep.root",
}
out_dir = "./plots"
color_baseline = ROOT.kBlue+2
color_variant = ROOT.kRed+2

os.makedirs(out_dir, exist_ok=True)


def get_histograms(input_file):
    # Load input file and init RDF
    df = ROOT.RDataFrame("events", input_file)

    df = (df
        .Define("track_dndx", "get_dndx_values(EFlowTrack_dNdx)")
        .Define("track_mtof", "get_track_mtofs(_EFlowTrack_trackStates, EFlowTrack_L, EFlowTrack.trackerHits_end, _EFlowTrack_trackerHits.index, TrackerHits.time)")
    )

    # Cluster-count (dN/dx) histogram -- adjust range once you've seen real values
    hist_dndx = df.Histo1D(
    ("hist_dndx", "Cluster count;dN/dx [clusters/m];Normalized entries (a.u.)", 100, 0.0, 5000.0),
    "track_dndx"
    )
    
    # Time-of-flight mass histogram, zoomed to show the low-mass (pion-scale) region
    hist_mtof = df.Histo1D(
        ("hist_mtof", "Track m_{TOF};m_{TOF} [GeV];Normalized entries (a.u.)", 100, 0.0, 1.0),
        "track_mtof"
    )

    return {"dndx": hist_dndx, "mtof": hist_mtof}


# Build histograms for every variant first, keeping them all in memory
all_hists = {prefix: get_histograms(f) for prefix, f in variants.items()}
baseline_hists = all_hists["baseline"]


def make_pairwise_plot(quantity, logscale, variant_prefix, variant_hists):
    c = ROOT.TCanvas(f"c_{quantity}_{variant_prefix}", "c", 800, 700)

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
    legend = ROOT.TLegend(0.68, 0.78, 0.88, 0.88)
    legend.SetFillStyle(0)
    legend.SetLineWidth(0)

    h_base = baseline_hists[quantity].GetValue().Clone(f"{quantity}_baseline_{variant_prefix}")
    h_base.SetDirectory(0)
    h_base.Scale(1.0 / h_base.Integral())
    h_base.SetLineColor(color_baseline)
    h_base.SetLineWidth(2)
    h_base.GetXaxis().SetLabelSize(0)
    h_base.GetXaxis().SetTitleSize(0)
    h_base.Draw("HIST")
    legend.AddEntry(h_base, "baseline", "l")

    h_var = variant_hists[quantity].GetValue().Clone(f"{quantity}_{variant_prefix}")
    h_var.SetDirectory(0)
    h_var.Scale(1.0 / h_var.Integral())
    h_var.SetLineColor(color_variant)
    h_var.SetLineWidth(2)
    h_var.Draw("HIST SAME")
    legend.AddEntry(h_var, variant_prefix, "l")

    legend.Draw()

    # --- Bottom pad: ratio of this variant to baseline ---
    pad_bot.cd()
    h_ratio = h_var.Clone(f"ratio_{quantity}_{variant_prefix}")
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

    c.SaveAs(f"{out_dir}/{variant_prefix}_vs_baseline_{quantity}.png")
    print(f"Written {out_dir}/{variant_prefix}_vs_baseline_{quantity}.png")


# One pairwise plot (baseline vs. variant) per non-baseline entry, per quantity
for variant_prefix, variant_hists in all_hists.items():
    if variant_prefix == "baseline":
        continue
    for quantity, logscale in [("dndx", False), ("mtof", False)]:
        make_pairwise_plot(quantity, logscale, variant_prefix, variant_hists)