# Open clock-distribution modification for phase-coherent RTL-SDR — code & data

Reproduction package for the HardwareX article *"An open clock-distribution
modification for phase-coherent operation of commodity RTL-SDR receivers."*
It contains the capture/analysis pipeline, the measurement data summaries, the
figures, and the build documentation for converting independent RTL-SDR dongles
into a phase-coherent group by injecting a shared Si5351A reference clock.

**Headline result (paired before/after on the same two receivers):**
inter-channel residual jitter **7.27 ± 3.26° → 0.08 ± 0.05°** (≥ 92×, floor-limited),
inter-channel beat **−250 Hz wandering → 0 Hz**, sample-clock ppm **+30/+27 → −27/−33**.

## Layout

```
capture/      # runs on the receiver host (Raspberry Pi)
  si5351_clk_28M8.py   # configure shared 28.8 MHz reference (CLK0)
  si5351_cw_100M.py    # configure CW test tone (100 MHz, CLK0+CLK1)
  record_campaign.py   # capture N paired 30 s IQ records per condition
analysis/     # runs anywhere with numpy
  coherence_lib.py     # core: IQ load, per-block beat tracking, jitter, floor, stats
  batch_analyze.py     # per-record jitter + summary stats + FM/drop-out filter
  characterize_floor.py# jitter vs integration window (noise floor)
  warmcheck.py         # quick capture+analyze (one short record) for bench checks
  export_phase.py      # export windowed inter-channel phase array (small CSV)
  make_synthetic.py    # synthetic IQ generator for pipeline self-test
journal/      # measurement_log.csv, per_unit_log.csv (ppm before/after)
results/      # *_metrics.csv, data figures (fig1–3)
figures/      # block diagram, bench setup, 74AC04 fan-out, Allan deviation
raw_iq/       # raw 30 s IQ records (large; not redistributed — regenerate or request)
```

## Method (one paragraph)

A common CW tone is presented to both receivers; the transmitter phase is
common-mode and cancels in the cross-power `a·conj(b)`. Per analysis block the
inter-channel frequency offset (*beat*) is estimated from the FFT peak of the
cross-power and derotated; the windowed cross-power phase (per-window DC removed)
is then linearly detrended within the block, and the residual standard deviation
is the **residual jitter**. For independent clocks the beat is large and wanders;
for a shared clock it is ≈ 0. The pipeline is validated against synthetic IQ
(recovers injected parameters to ≈ 1 %; floor slope −0.53 vs CRB −0.5).

## Quick start

```bash
# on the host: bring up the shared clock and the CW test tone
sudo python3 capture/si5351_clk_28M8.py        # shared 28.8 MHz reference
sudo python3 capture/si5351_cw_100M.py         # CW test tone

# capture and analyse
python3 capture/record_campaign.py --condition baseline --runs 12 \
    --dev-a 0 --dev-b 1 --gain 32.8 --freq 99.8e6 --len 30 --out raw_iq
python3 analysis/batch_analyze.py --raw raw_iq --condition baseline
python3 analysis/characterize_floor.py --rec raw_iq/shared_run04
```

## Licenses

Code: MIT (`LICENSE`). Hardware design files: CERN-OHL-S v2. Documentation/figures/data: CC-BY 4.0.

## Citation

[TODO: add article DOI / Zenodo DOI on acceptance.]
