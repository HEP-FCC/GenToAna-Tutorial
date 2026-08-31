import ROOT

# global parameters
intLumi        = VALUE #in pb-1
ana_tex        = 'pp #rightarrow HH #rightarrow b #bar{b} #gamma #gamma '
delphesVersion = '3.4.2'
energy         = VALUE
collider       = 'FCC-hh'
inputDir       = 'path'
formats        = ['png','pdf']
yaxis          = ['lin','log']
stacksig       = ['nostack']
outdir         = 'path'
plotStatUnc    = True

variables = ['your_observables'] #these should match keys from histoList in your final-stage script

# rebin = [1, 1, 1, 1, 2] # uniform rebin per variable (optional)

### Dictionary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections['your_analysis_name']   = ["your_selections"]

# Labelling your selections: remember extralabel keys must match the cut names you defined in cutList.
extralabel = {}
extralabel['sel0_example'] = "Here we selected 1 == 1"

colors = {}
colors['process_short_name'] = ROOT.kRed

plots = {}
plots['your_analysis_name'] = {'signal':{'process_short_name':['sample_name']},
           }

legend = {}
legend['process_short_name'] = 'process'