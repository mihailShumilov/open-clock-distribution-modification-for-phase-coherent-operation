import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
TAU0=0.1  # базовое окно фазы 100мс
def load(f):
    d=np.genfromtxt(f,delimiter=",",names=True); return d["phase_deg"]
def struct_fn(ph,tau0=TAU0):
    # RMS изменения межканальной фазы за интервал tau = m*tau0 (Allan-type structure function)
    N=len(ph); taus=[]; D=[]
    m=1
    while m< N//3:
        diffs=ph[m:]-ph[:-m]
        D.append(np.sqrt(np.mean(diffs**2))); taus.append(m*tau0); m=int(np.ceil(m*1.5))
    return np.array(taus),np.array(D)
base=load("baseline_run01_phase.csv")
shar=load("shared_run04_phase.csv")
tb,Db=struct_fn(base); ts,Ds=struct_fn(shar)
fig,ax=plt.subplots(figsize=(6.2,4.6))
ax.loglog(tb,Db,"o-",color="#d62728",label="baseline (independent TCXOs)")
ax.loglog(ts,Ds,"s-",color="#1f77b4",label="shared clock")
ax.set_xlabel("Averaging interval  tau, s")
ax.set_ylabel("RMS inter-channel phase change, deg")
ax.set_title("Inter-channel phase stability (Allan-type structure function)")
ax.grid(True,which="both",alpha=0.3); ax.legend()
# аннотация выигрыша на tau=1s
import numpy as _n
def at(t,D,tt): i=int(_n.argmin(_n.abs(t-tt))); return D[i]
b1=at(tb,Db,1.0); s1=at(ts,Ds,1.0)
ax.annotate(f"~{b1/s1:.0f}x at tau=1 s",xy=(1.0,s1),xytext=(1.4,s1*6),fontsize=9,
            arrowprops=dict(arrowstyle="->",color="#444"))
fig.tight_layout(); fig.savefig("../figures/fig_allan_deviation.png",dpi=200)
print(f"ADEV ok | baseline@1s={b1:.1f} deg, shared@1s={s1:.3f} deg, ratio {b1/s1:.0f}x")
print(f"shared short-tau (0.1s)={Ds[0]:.3f} deg  baseline short-tau={Db[0]:.2f} deg")
