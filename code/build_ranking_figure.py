from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument("--analysis", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
d = json.loads(args.analysis.read_text())
args.output_dir.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":12, "svg.fonttype":"none", "pdf.fonttype":42})
ink, muted, teal, violet, amber = "#193039", "#61717A", "#13766E", "#6B5A94", "#A46625"
fig = plt.figure(figsize=(14, 11), facecolor="#FAF9F5")
fig.text(.055,.965,"MUSE SHOPPING / RANKING MATH / SAVED OBSERVATIONS",fontsize=11,color=muted,weight="bold")
fig.text(.055,.916,"A visible score does not determine the whole order",fontsize=25,color=ink,weight="bold")
fig.text(.055,.88,"Actual score profiles and controlled input comparisons; no recovered production weights.",fontsize=13,color=muted)


def profile(rect, source, title, subtitle):
    ax=fig.add_axes(rect,facecolor="white")
    rows=source["products"]
    x=[p["position"] for p in rows]
    y=[float(p["ranking_score"]) for p in rows]
    ax.plot(x,y,color=teal,marker="o",markersize=3,linewidth=1.7)
    ax.set_ylim(.2,.9)
    ax.set_yticks([.2,.4,.6,.8])
    ax.set_xlim(0,len(rows)+2)
    ax.set_ylabel("Visible numeric score",color=muted)
    ax.set_xlabel("Returned position",color=muted)
    ax.grid(axis="y",color="#E2E6E5",linewidth=.7)
    for s in ["top","right"]:ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#CBD1D1")
    ax.spines["bottom"].set_color("#CBD1D1")
    ax.tick_params(colors=muted)
    ax.set_title(title,loc="left",fontweight="bold",color=ink,pad=40,fontsize=16)
    ax.text(0,1.05,subtitle,transform=ax.transAxes,color=muted,fontsize=11)
    return ax


a=profile([.075,.555,.38,.245],d["neutral"],"01  A late score jump","Neutral pan query · 43 returned records")
a.scatter([40,41],[.558594,.773438],s=50,color=amber,zorder=5)
a.annotate("Quince: #41, score 0.773438",xy=(41,.773438),xytext=(4,.88),textcoords="data",fontsize=10.5,color=amber,arrowprops={"arrowstyle":"-","color":amber})
a.annotate("#40: 0.558594",xy=(40,.558594),xytext=(18,.30),fontsize=10.5,color=amber,arrowprops={"arrowstyle":"-","color":amber})
fig.text(.075,.478,"Score-only sorting of this same saved list puts Quince at #20.\nThat is a counterfactual calculation, not a new recommendation.",fontsize=10.5,color=muted,linespacing=1.4)

b=profile([.565,.555,.38,.245],d["levoit"],"02  A domain boundary is not the whole rule","Levoit + brand flag · 50 returned records")
b.axvspan(.5,16.5,color=violet,alpha=.09)
b.axvline(16.5,color=violet,linestyle="--",linewidth=1)
b.scatter([16,17],[.382812,.808594],s=45,color=violet,zorder=5)
b.annotate("16 → 17: +0.425782",xy=(17,.808594),xytext=(22,.87),fontsize=10.5,color=violet,arrowprops={"arrowstyle":"-","color":violet})
b.text(2,.26,"16-item target-domain prefix",fontsize=9.5,color=violet)
fig.text(.565,.478,"A later increase also occurs inside the other-domain suffix.\nAcross strong-brand cases, group-then-score fails in 12 of 18.",fontsize=10.5,color=muted,linespacing=1.4)

c=fig.add_axes([.055,.15,.43,.245])
c.axis("off")
c.text(0,1.11,"03  Nine places higher, with a lower score",fontsize=16,color=ink,weight="bold",transform=c.transAxes)
c.text(0,.98,"Hydro Flask Palmer Green · each condition repeated 3 times",fontsize=10.5,color=muted,transform=c.transAxes)
table=c.table(cellText=[["Baseline","15","0.753906","40"],["+ brand flag","6","0.750000","47"]],
               colLabels=["Condition","Position","Score","Records"],cellLoc="left",colLoc="left",bbox=[0,.36,1,.49],colWidths=[.38,.2,.25,.17])
table.auto_set_font_size(False)
table.set_fontsize(12)
for (row,col),cell in table.get_celld().items():
    cell.set_edgecolor("#D8DFDE")
    cell.set_linewidth(.7)
    cell.set_text_props(color=ink)
    cell.set_facecolor("#EDF4F1" if row==0 else "white")
    if row==0:cell.set_text_props(weight="bold")
c.text(0,.17,r"$\Delta r=-9$     $\Delta s=-0.003906$",fontsize=18,color=teal,transform=c.transAxes)
c.text(0,-.04,"The candidate pool also changes; this is not a fixed-list reorder.",fontsize=10.5,color=muted,transform=c.transAxes)

e=fig.add_axes([.565,.15,.38,.245])
e.axis("off")
e.text(0,1.11,"04  Combining visible lists is insufficient",fontsize=16,color=ink,weight="bold",transform=e.transAxes)
e.text(0,.98,"Pan + skillet query arguments · same composition in 3 repeats",fontsize=10.5,color=muted,transform=e.transAxes)
start=0
for n,color,label in [(27,teal,"27 from A"),(26,violet,"26 from B"),(3,amber,"3")]:
    e.barh(.65,n,left=start,height=.18,color=color)
    e.text(start+n/2,.65,label,ha="center",va="center",color="white",fontsize=11,weight="bold")
    start+=n
e.set_xlim(0,56)
e.set_ylim(0,1)
e.text(0,.39,"3 IDs absent from both visible solo outputs",fontsize=12,color=amber,weight="bold")
e.text(0,.19,r"$56 = 27 + 26 + 3$",fontsize=20,color=ink)
e.text(0,-.04,"AB vs one joined string: 5 shared IDs / 99 union IDs (5.05%).",fontsize=10.5,color=muted)

fig.text(.055,.052,"Different examples and query conditions; not stages of one execution. Score calibration is unestablished.\nSources and exact decimals are retained in analysis.json. Origin/runtime limitations remain.  |  Astra (gpt-6-astra)",fontsize=10,color=muted,linespacing=1.5)
for ext in ("png","svg","pdf"):
    fig.savefig(args.output_dir/f"ranking-math.{ext}",dpi=160,facecolor=fig.get_facecolor(),
                metadata={"Creator":"Astra (gpt-6-astra)"} if ext!="png" else {"Author":"Astra (gpt-6-astra)"})
plt.close(fig)
print("Saved the ranking evidence figure as PNG, SVG and PDF.")
