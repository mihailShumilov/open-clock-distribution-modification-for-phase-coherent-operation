import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np
OUT="../figures/"
BLUE="#1f77b4"; RED="#d62728"; GREY="#555"; GREEN="#2a8a3e"; BOX="#eef3fb"; BOXE="#3b6fb0"

def box(ax,x,y,w,h,txt,fc=BOX,ec=BOXE,fs=9,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.06",
        fc=fc,ec=ec,lw=1.4))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=fs,fontweight="bold" if bold else "normal")
def arr(ax,x1,y1,x2,y2,c=GREY,ls="-",lw=1.6):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,color=c,lw=lw,ls=ls))
def ant(ax,x,y):
    ax.plot([x,x],[y,y+0.25],color=GREY,lw=1.4)
    ax.plot([x-0.12,x,x+0.12],[y+0.45,y+0.25,y+0.45],color=GREY,lw=1.4)

# ============ Fig 1: block diagram (stock vs shared) ============
fig,(a1,a2)=plt.subplots(1,2,figsize=(10,4.6))
for ax in (a1,a2): ax.set_xlim(0,6); ax.set_ylim(0,6); ax.axis("off")
# (a) baseline
a1.set_title("(a) Stock: independent oscillators",fontsize=11,fontweight="bold")
ant(a1,1.4,4.7); ant(a1,4.0,4.7)
box(a1,0.5,3.6,1.8,1.0,"RTL-SDR #1\nTCXO (own)")
box(a1,3.1,3.6,1.8,1.0,"RTL-SDR #2\nTCXO (own)")
arr(a1,1.4,3.6,1.9,2.4); arr(a1,4.0,3.6,3.6,2.4)
box(a1,1.6,1.4,2.3,1.0,"Host (Raspberry Pi)\nUSB capture")
a1.text(3.0,0.7,"independent LO -> inter-channel\nphase rotates, beat != 0",ha="center",va="center",
        fontsize=8.5,color=RED,style="italic")
# (b) shared
a2.set_title("(b) Modified: shared reference clock",fontsize=11,fontweight="bold")
ant(a2,1.4,4.7); ant(a2,4.0,4.7)
box(a2,0.5,3.6,1.8,1.0,"RTL-SDR #1\nclk injected")
box(a2,3.1,3.6,1.8,1.0,"RTL-SDR #N\nclk injected")
box(a2,1.9,5.05,2.2,0.7,"Si5351A  28.8 MHz",fc="#eaf6ea",ec=GREEN)
# clock distribution
a2.add_patch(FancyArrowPatch((3.0,5.05),(3.0,4.85),arrowstyle="-",color=GREEN,lw=1.6))
a2.plot([1.4,4.6],[4.85,4.85],color=GREEN,lw=1.6)
arr(a2,1.4,4.85,1.4,4.6,c=GREEN); arr(a2,4.0,4.85,4.0,4.6,c=GREEN)
a2.text(4.75,4.85,"CLK0",fontsize=8,color=GREEN,va="center")
arr(a2,1.4,3.6,1.9,2.4); arr(a2,4.0,3.6,3.6,2.4)
box(a2,1.6,1.4,2.3,1.0,"Host (Raspberry Pi)\nI2C clock cfg + USB")
a2.text(3.0,0.7,"common reference -> coherent,\nbeat = 0 (fixed offset calibrated)",ha="center",va="center",
        fontsize=8.5,color=GREEN,style="italic")
fig.suptitle("Figure 1. Clock-injection modification: independent vs shared reference",fontsize=12,fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig(OUT+"fig_block_diagram.png",dpi=200); print("block ok")

# ============ Bench setup ============
fig,ax=plt.subplots(figsize=(8.5,5.2)); ax.set_xlim(0,10); ax.set_ylim(0,7); ax.axis("off")
box(ax,4.0,0.4,2.0,0.9,"Raspberry Pi 5",fc="#f0f0f0",ec=GREY,bold=True)
# receivers
ant(ax,1.6,4.2); ant(ax,3.0,4.2)
box(ax,0.8,3.1,1.5,0.9,"RTL-SDR\n#3 (dev0)"); box(ax,2.4,3.1,1.5,0.9,"RTL-SDR\n#4 (dev1)")
arr(ax,1.55,3.1,4.4,1.3); arr(ax,3.15,3.1,4.7,1.3)
ax.text(2.0,2.0,"USB",fontsize=8,color=GREY)
# Si5351 #1 clock
box(ax,0.6,5.2,2.2,0.8,"Si5351A #1\n28.8 MHz clock",fc="#eaf6ea",ec=GREEN)
ax.plot([1.55,1.55],[5.2,4.0],color=GREEN,lw=1.6); ax.plot([3.15,3.15],[5.2,4.0],color=GREEN,lw=1.6)
ax.plot([1.55,3.15],[5.2,5.2],color=GREEN,lw=1.6)
arr(ax,1.55,4.3,1.55,4.0,c=GREEN); arr(ax,3.15,4.3,3.15,4.0,c=GREEN)
ax.text(3.4,4.6,"CLK0 injection",fontsize=8,color=GREEN)
arr(ax,2.8,5.6,4.0,1.0,c=GREEN,ls=":"); ax.text(3.6,3.6,"I2C",fontsize=7.5,color=GREEN)
# Si5351 #2 CW
box(ax,6.8,5.0,2.6,0.9,"Si5351A #2\nCW 100.0 MHz",fc="#fdeaea",ec=RED)
ant(ax,7.0,4.0)
ax.plot([8.1,7.0],[5.0,4.45],color=RED,lw=1.6); ax.text(7.2,4.7,"radiator",fontsize=7.5,color=RED)
# over-air
for xx in (4.0,4.6,5.2):
    ax.add_patch(plt.matplotlib.patches.Arc((7.0,4.3),xx,xx,angle=0,theta1=150,theta2=250,color=RED,lw=1,ls=":"))
ax.text(5.2,4.9,"over-air CW",fontsize=8,color=RED,style="italic")
arr(ax,6.6,5.4,6.0,1.0,c=RED,ls=":"); ax.text(6.0,3.6,"I2C",fontsize=7.5,color=RED)
ax.set_title("Bench setup: shared-clock injection + common CW test tone (over-air)",fontsize=11,fontweight="bold")
fig.tight_layout(); fig.savefig(OUT+"fig_bench_setup.png",dpi=200); print("bench ok")

# ============ Fan-out 74AC04 schematic ============
fig,ax=plt.subplots(figsize=(8.5,5.0)); ax.set_xlim(0,10); ax.set_ylim(0,7); ax.axis("off")
# input
box(ax,0.3,3.0,1.8,0.8,"Si5351A\nCLK0 28.8MHz",fc="#eaf6ea",ec=GREEN)
# 74AC04 body
ax.add_patch(Rectangle((3.2,1.0),2.2,5.0,fc="#eef3fb",ec=BOXE,lw=1.5))
ax.text(4.3,6.2,"74AC04",ha="center",fontsize=10,fontweight="bold")
ax.text(4.3,5.75,"hex inverter",ha="center",fontsize=8,color=GREY)
# input buffer inverter (gate1) + 5 output inverters in parallel
def inv(ax,x,y,lbl=""):
    ax.add_patch(plt.Polygon([[x,y-0.18],[x,y+0.18],[x+0.36,y]],closed=True,fc="white",ec=BOXE,lw=1.2))
    ax.add_patch(plt.Circle((x+0.42,y),0.06,fc="white",ec=BOXE,lw=1.2))
# stage 1 buffer
arr(ax,2.1,3.4,3.5,3.4,c=GREY)
inv(ax,3.5,3.4); ax.text(3.7,3.0,"buffer",fontsize=7,color=GREY)
ax.plot([3.98,4.6],[3.4,3.4],color=GREY,lw=1.4)
ax.plot([4.6,4.6],[1.5,5.3],color=GREY,lw=1.4)  # distribution rail
# 5 output inverters
ys=[1.6,2.5,3.4,4.3,5.2]
for i,y in enumerate(ys):
    ax.plot([4.6,4.9],[y,y],color=GREY,lw=1.2)
    inv(ax,4.9,y)
    ax.plot([5.38,6.2],[y,y],color=GREY,lw=1.2)
    box(ax,6.2,y-0.32,2.4,0.64,f"RTL-SDR #{i+1}  (clk in)",fs=8)
# Vcc + decoupling
ax.plot([4.3,4.3],[6.0,6.5],color=RED,lw=1.4); ax.text(4.3,6.62,"Vcc 3.3V",ha="center",fontsize=7.5,color=RED)
ax.plot([4.3,4.3],[1.0,0.5],color="k",lw=1.4); ax.text(4.3,0.36,"GND",ha="center",fontsize=7.5)
ax.plot([7.0,7.0],[6.4,6.0],color=RED,lw=1.2); ax.text(7.5,6.2,"100nF decoupling",fontsize=7.5,color=RED,va="center")
ax.plot([6.9,7.1],[6.0,6.0],color="k",lw=1.4); ax.plot([6.92,7.08],[5.92,5.92],color="k",lw=1.4)
ax.plot([7.0,7.0],[5.92,5.6],color="k",lw=1.0)
ax.set_title("Clock fan-out buffer (74AC04, 1->5) for arrays >2 channels",fontsize=11,fontweight="bold")
ax.text(5.0,0.1,"Schematic representation; KiCad source [TODO].",ha="center",fontsize=7.5,color=GREY,style="italic")
fig.tight_layout(); fig.savefig(OUT+"fig_fanout_74ac04.png",dpi=200); print("fanout ok")
