from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT = Path(__file__).resolve().parents[1]
fig, ax = plt.subplots(figsize=(11, 4.6)); ax.axis('off'); ax.set_xlim(0, 11); ax.set_ylim(0, 4.6)
def box(x, y, w, h, title, body, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03', fc=fc, ec='#1f4e79', lw=1.2))
    ax.text(x+w/2, y+h-0.18, title, ha='center', va='top', fontsize=9, fontweight='bold')
    ax.text(x+w/2, y+h-0.55, body, ha='center', va='top', fontsize=7.4, linespacing=1.25)
def arrow(x1, y1, x2, y2): ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#444', lw=1.3))
box(0.1, 2.7, 2.3, 1.7, '1. GOAL & BOUNDARY', 'Forecast S&P 500 price-index\nclose, 20 Nov 2026.\nUse data <= 12 Nov 2026 close\n(cutoff 13 Nov 12:00 London).', '#e8f0f8')
box(2.8, 2.7, 2.3, 1.7, '2. DATA (observed)', 'Daily ^GSPC closes 2018-2026\n(CSV snapshot, 2,229 rows,\nSHA-256 recorded).\nSource and hash logged;\nretrieval time unlogged/disclosed.', '#e8f0f8')
box(5.5, 2.7, 2.3, 1.7, '3. TOOLS (calculation)', 'Python: RV20 factor, rolling\nOLS, backtest vs benchmarks,\nNewey-West tests, sensitivity.', '#eef6ea')
box(8.2, 2.7, 2.6, 1.7, '4. AGENT DECISIONS', 'Choose RV20 OLS (lowest pooled\nMAPE of 4 simple models);\nrefit at 8-day horizon;\nno discretionary adjustment.', '#fdf3e0')
box(7.7, 0.2, 3.1, 1.9, '5. FORECAST (model calculation)', 'Baseline 7,592.40\n+ drift +21.84 pts\n+ RV20 effect +13.17 pts\n= 7,627.41 index points', '#eef6ea')
box(3.9, 0.2, 3.4, 1.9, '6. CHECKS (independent)', 'Label timing: training targets <= origin\nHand re-calculation: 7592.40 x 1.004611\nRe-run of script gives same forecast\nOwn HAC re-computation matches\nCutoff error (10:00 vs 12:00) corrected', '#fbeaea')
box(0.1, 0.2, 3.4, 1.9, '7. HUMAN RESPONSIBILITY', 'Sole author reviews data, code,\nlimits and provenance, approves\nand takes responsibility for the\nsubmitted forecast. Frozen files.', '#f3e9f7')
for a in ((2.4,3.55,2.8,3.55),(5.1,3.55,5.5,3.55),(7.8,3.55,8.2,3.55),(9.5,2.7,9.5,2.12),(7.7,1.15,7.3,1.15),(3.9,1.15,3.5,1.15)): arrow(*a)
plt.savefig(ROOT/'08_Evidence/workflow_diagram.png', dpi=170, bbox_inches='tight')
