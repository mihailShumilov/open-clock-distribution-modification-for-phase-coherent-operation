import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

# --- ИЗМЕРЕННЫЕ ДАННЫЕ (с Pi, пара #3+#4, 2026-06-08) ---
baseline = [15.353,5.781,8.215,5.816,9.298,8.376,6.254,2.511,7.115,3.443,6.451,8.676]  # n=12
# shared серия 2; прогоны 7,9,11 — артефакты захвата (FM/USB-дроп), исключены
shared_all = {1:0.064,2:0.084,3:0.090,4:0.044,5:0.081,6:0.051,7:7.013,8:0.041,9:4.688,10:0.245,11:11.481,12:0.067}
shared = [v for k,v in shared_all.items() if k not in (7,9,11)]  # чистые n=9
# + чистые из серии 1 для общей оценки
shared_s1 = [0.094,0.084,0.071,0.052,0.052,0.046,0.103,0.077]
shared_clean_all = shared + shared_s1  # 17 чистых

def stats(x):
    x=np.array(x); n=len(x); m=x.mean(); s=x.std(ddof=1); ci=1.96*s/np.sqrt(n)
    return n,m,s,ci
bn,bm,bs,bci = stats(baseline)
sn,sm,ss,sci = stats(shared)
an,am,asd,aci = stats(shared_clean_all)
fac = bm/am
print(f"baseline: n={bn}  {bm:.2f} ± {bs:.2f}° (CI ±{bci:.2f})")
print(f"shared(сер.2 чистые): n={sn}  {sm:.3f} ± {ss:.3f}° (CI ±{sci:.3f})")
print(f"shared(все чистые):   n={an}  {am:.3f} ± {asd:.3f}° (CI ±{aci:.3f})")
print(f"улучшение: ×{fac:.0f}")

# floor sweep (shared_run04)
fw_win=[2,5,10,20,50,100,200]; fw_j=[2.0488,0.9545,0.1912,0.1395,0.1026,0.0787,0.0636]
fw_N=[int(2.4e6*w/1000) for w in fw_win]

# ---- Fig 1: jitter по состояниям ----
fig,ax=plt.subplots(figsize=(5.6,4.3))
for i,(name,data,col) in enumerate([("baseline\n(свои TCXO)",baseline,"#d62728"),("shared\n(общий клок)",shared,"#1f77b4")]):
    d=np.array(data); x=np.full(len(d),i)+np.random.uniform(-0.06,0.06,len(d))
    ax.scatter(x,d,s=34,alpha=0.75,color=col,zorder=3)
    m,sd=d.mean(),d.std(ddof=1)
    ax.errorbar(i,m,yerr=sd,fmt="_",color="k",capsize=7,markersize=26,lw=1.6,zorder=4)
    ax.annotate(f"{m:.2f}±{sd:.2f}°" if m>1 else f"{m:.3f}±{sd:.3f}°",(i,m),
                textcoords="offset points",xytext=(16,0),va="center",fontsize=9,fontweight="bold")
ax.set_yscale("log"); ax.set_xticks([0,1]); ax.set_xticklabels(["baseline\n(свои TCXO)","shared\n(общий клок)"])
ax.set_ylabel("Остаточный межканальный джиттер, ° (log)")
ax.set_title(f"Когерентность пары RTL-SDR #3+#4\nулучшение ×{fac:.0f}  (n={bn}/{sn})")
ax.grid(True,axis="y",which="both",alpha=0.3); fig.tight_layout()
fig.savefig("fig1_jitter_baseline_vs_shared.png",dpi=200); print("→ fig1")

# ---- Fig 2: floor curve ----
fig,ax=plt.subplots(figsize=(6,4.3))
ax.loglog(fw_win,fw_j,"o-",color="#1f77b4",label="Измерено (shared_run04)")
# опорная 1/sqrt(N) через точку 100мс
ref=[0.0787*np.sqrt(240000/n) for n in fw_N]
ax.loglog(fw_win,ref,"--",color="#888",label="∝ 1/√N (CRB-наклон −0.5)")
ax.axhline(7.27,color="#d62728",ls=":",lw=1.3,label="baseline 7.3° (для масштаба)")
ax.set_xlabel("Окно интегрирования, мс"); ax.set_ylabel("Остаточный джиттер, °")
ax.set_title("Шумовой порог замера: shared падает ∝1/√N\n(полка не достигнута → джиттер ≤ floor)")
ax.grid(True,which="both",alpha=0.3); ax.legend(fontsize=8); fig.tight_layout()
fig.savefig("fig2_floor_curve.png",dpi=200); print("→ fig2")

# ---- таблица .md ----
with open("article_table_DRAFT.md","w") as f:
    f.write("# Статья 1 — итоговая таблица (пара #3+#4, парный before/after)\n\n")
    f.write("| Состояние | n | Межкан. джиттер, ° (mean±σ) | 95% CI | Бит, Гц | PPM |\n")
    f.write("|---|---|---|---|---|---|\n")
    f.write(f"| Baseline (свои TCXO) | {bn} | {bm:.2f} ± {bs:.2f} | ±{bci:.2f} | −70…−267 (гуляет ±7–25) | +30 / +27 |\n")
    f.write(f"| Shared (общий клок) | {sn} | {sm:.3f} ± {ss:.3f} | ±{sci:.3f} | 0.0 ± 0.0 | −27 / −33 |\n\n")
    f.write(f"**Улучшение джиттера:** ×{fac:.0f} (нижняя оценка — shared на шумовом полу).\n\n")
    f.write(f"**Шумовой порог:** джиттер падает ∝1/√N до ≥200 мс без полки → истинная когерентность ≤ floor.\n\n")
    f.write(f"Все чистые shared-записи (2 серии): n={an}, {am:.3f} ± {asd:.3f}°.\n")
print("→ article_table_DRAFT.md")
