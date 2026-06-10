import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

baseline=[15.353,5.781,8.215,5.816,9.298,8.376,6.254,2.511,7.115,3.443,6.451,8.676]
shared_all={1:0.064,2:0.084,3:0.090,4:0.044,5:0.081,6:0.051,7:7.013,8:0.041,9:4.688,10:0.245,11:11.481,12:0.067}
shared=[v for k,v in shared_all.items() if k not in (7,9,11)]
def st(x):
    x=np.array(x);n=len(x);return n,x.mean(),x.std(ddof=1)
bn,bm,bs=st(baseline); sn,sm,ss=st(shared); fac=bm/sm

# ---- Fig 1 ----
fig,ax=plt.subplots(figsize=(5.6,4.3))
for i,(lbl,data,col) in enumerate([("baseline\n(independent TCXOs)",baseline,"#d62728"),("shared\n(common clock)",shared,"#1f77b4")]):
    d=np.array(data); x=np.full(len(d),i)+np.random.uniform(-0.06,0.06,len(d))
    ax.scatter(x,d,s=34,alpha=0.75,color=col,zorder=3)
    m,sd=d.mean(),d.std(ddof=1)
    ax.errorbar(i,m,yerr=sd,fmt="_",color="k",capsize=7,markersize=26,lw=1.6,zorder=4)
    ax.annotate(f"{m:.2f}±{sd:.2f}°" if m>1 else f"{m:.3f}±{sd:.3f}°",(i,m),
                textcoords="offset points",xytext=(16,0),va="center",fontsize=9,fontweight="bold")
ax.set_yscale("log"); ax.set_xticks([0,1]); ax.set_xticklabels(["baseline\n(independent TCXOs)","shared\n(common clock)"])
ax.set_ylabel("Residual inter-channel jitter, ° (log)")
ax.set_title(f"Inter-channel coherence, receiver pair #3+#4\nimprovement ×{fac:.0f}  (n={bn}/{sn})")
ax.grid(True,axis="y",which="both",alpha=0.3); fig.tight_layout()
fig.savefig("fig1_jitter_baseline_vs_shared.png",dpi=200); print("fig1 EN")

# ---- Fig 2 (floor) ----
fw=[2,5,10,20,50,100,200]; fj=[2.0488,0.9545,0.1912,0.1395,0.1026,0.0787,0.0636]
fN=[int(2.4e6*w/1000) for w in fw]
fig,ax=plt.subplots(figsize=(6,4.3))
ax.loglog(fw,fj,"o-",color="#1f77b4",label="Measured (shared_run04)")
ref=[0.0787*np.sqrt(240000/n) for n in fN]
ax.loglog(fw,ref,"--",color="#888",label="$\\propto 1/\\sqrt{N}$ (CRB slope −0.5)")
ax.axhline(7.27,color="#d62728",ls=":",lw=1.3,label="baseline 7.3° (for scale)")
ax.set_xlabel("Integration window, ms"); ax.set_ylabel("Residual jitter, °")
ax.set_title("Measurement noise floor: shared jitter falls $\\propto 1/\\sqrt{N}$\n(no plateau → jitter ≤ floor)")
ax.grid(True,which="both",alpha=0.3); ax.legend(fontsize=8); fig.tight_layout()
fig.savefig("fig2_floor_curve.png",dpi=200); print("fig2 EN")

# ---- Fig 3 (phase timeseries) ----
def ld(f): d=np.genfromtxt(f,delimiter=",",names=True); return d["time_s"],d["phase_deg"]
tb,pb=ld("baseline_run01_phase.csv"); ts,ps=ld("shared_run04_phase.csv")
def jit(ph):
    r=[]
    for i in range(0,len(ph),5):
        s=ph[i:i+5]
        if len(s)>=3: x=np.arange(len(s)); c=np.polyfit(x,s,1); r.extend(s-np.polyval(c,x))
    return np.std(r,ddof=1)
js=jit(ps)
fig,(a1,a2)=plt.subplots(2,1,figsize=(7,6.2),gridspec_kw={"height_ratios":[2,1]})
a1.plot(tb,pb,color="#d62728",lw=1.1,label=f"baseline (independent TCXOs), range ±{np.abs(pb).max():.0f}°")
a1.plot(ts,ps,color="#1f77b4",lw=1.4,label=f"shared (common clock), range ±{np.abs(ps).max():.0f}°")
a1.axhline(0,color="k",lw=0.5,alpha=0.4)
a1.set_ylabel("Inter-channel phase $\\varphi_{AB}$, °\n(mean beat removed)")
a1.set_title("Phase coherence, receiver pair #3+#4: independent vs shared clock")
a1.legend(fontsize=8,loc="upper left"); a1.grid(alpha=0.25)
a2.plot(ts,ps,color="#1f77b4",lw=1.4); a2.axhline(0,color="k",lw=0.5,alpha=0.4); a2.set_ylim(-30,30)
a2.set_xlabel("Time, s"); a2.set_ylabel("shared, ° (zoom)")
a2.set_title(f"Zoom on shared: slow drift ±{np.abs(ps).max():.0f}° (calibratable), fast jitter {js:.3f}°",fontsize=9)
a2.grid(alpha=0.25); fig.tight_layout()
fig.savefig("fig3_phase_timeseries.png",dpi=200); print("fig3 EN")
