# A. burtoni Social Influence — Track Visualiser

Interactive animation of cichlid fish movement trajectories, based on data from:

> **Dominant and subordinate males show context-dependent differences in social influence**  
> Jordan Lab — [Dataset on Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.qz612jmbz#usage)

---

## Background

This repository visualises tracking data from a study on social influence in the cichlid fish _Astatotilapia burtoni_. The study asks a simple but non-obvious question: does being the most dominant individual in a group make you the most influential in all situations?

The short answer is no. Dominant males — identifiable by bright colouration and aggressive behaviour — drive everyday group movement effectively. But in a group learning task, where a knowledgeable fish must teach naïve group members to associate a coloured light with food, **subordinate males are significantly better teachers**. The reason comes down to signal-to-noise ratio: dominant males move fast and erratically as a baseline, so their informative behaviour is hard to distinguish from their normal activity. Subordinate males are calmer and stay physically closer to the group, making their signals easier to read and follow.

The study used overhead video and deep-learning-based tracking (Mask R-CNN) to record the position of every fish in every frame, building social networks from who initiates movement and who follows.

---

## Data

Data is sourced from the [Dryad repository](https://datadryad.org/dataset/doi:10.5061/dryad.qz612jmbz#usage) and consists of four CSV files:

### `tracks_T3.csv`

Raw positional tracking data for one trial. Each row is one fish at one video frame.

| Column      | Description                             |
| ----------- | --------------------------------------- |
| `FRAME_IDX` | Video frame number (0-indexed)          |
| `X`         | Horizontal position in pixels           |
| `Y`         | Vertical position in pixels (top = 0)   |
| `IDENTITY`  | Fish ID (0–9), consistent across frames |

- **39,593 rows** across **4,165 frames** and **10 fish**
- Not every fish appears in every frame — detection coverage is ~94.8% after manual correction
- Identity assignment between frames uses a distance-based nearest-neighbour approach: each detection is matched to the closest detection in the previous frame

### `social_parameters.csv`

Behavioural metrics computed from the tracking data for each fish in each of six observation groups, comparing dominant and subordinate males.

| Column            | Description                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------------- |
| `centrality`      | Out-edge Katz centrality — how much others react to this fish's movement                     |
| `aa_out`          | Mean angular area subtended on groupmates' retinas (degrees) — visual connectedness          |
| `pairwise_dist`   | Mean distance to all other group members (normalised)                                        |
| `noise_frequency` | Proportion of time spent in fast directed movement above the 95th percentile speed threshold |
| `social_status`   | `DOM` (dominant) or `SUB` (subordinate)                                                      |
| `trial`           | Observation group index (0–5)                                                                |

Dominant males have significantly higher centrality and noise frequency. Subordinate males are physically closer to the group and subtend a slightly larger visual angle — they are calmer and easier to attend to.

### `learning.csv`

Group-level outcomes from the association learning task. Groups had to learn that one of two coloured LEDs (yellow-orange vs cyan) predicted food delivery.

| Column            | Description                                                                                                     |
| ----------------- | --------------------------------------------------------------------------------------------------------------- |
| `REPLICATE`       | Group replicate (1–7)                                                                                           |
| `STATUS`          | Condition: `0` = naïve control, `1–3` = subordinate informant replicates, `4–5` = dominant informant replicates |
| `DEMONSTRATOR`    | `0` = no informant, `1` = subordinate, `2` = dominant                                                           |
| `TRIAL`           | Trial number at which group consensus was reached                                                               |
| `7 RESPOND TWICE` | `1` if the group met the criterion (7/8 fish responding correctly in 2 consecutive trials)                      |
| `SURVIVAL`        | `1` if the group completed the task within 20 trials (used for Kaplan-Meier survival analysis)                  |

Groups with a subordinate informant reached consensus in ~9 trials on average (100% completion rate). Groups with a dominant informant took ~13.8 trials. Naïve groups with no informant took ~18.6 trials.

### `delay_times.csv`

Pairwise response delay times — the lag in frames between one fish initiating a fast movement and a second fish crossing the same speed threshold.

| Column          | Description                                                                           |
| --------------- | ------------------------------------------------------------------------------------- |
| `delay`         | Number of frames between initiator crossing speed threshold and responder crossing it |
| `id`            | Fish ID of the initiator                                                              |
| `social_status` | `DOM` or `SUB` — social status of the initiator                                       |

A delay of 0 means the responder moved simultaneously. Dominant males have a 71% zero-delay rate (others react to them immediately and often pre-emptively), versus 43% for subordinates — confirming that dominants drive routine group movement.

---

## Visualiser

### Setup

```
project/
    serve_animation.py
    data/
        tracks_T3.csv
        delay_times.csv
        learning.csv
        social_parameters.csv
```

No external dependencies. Requires Python 3.6+.

```bash
python serve_animation.py
```

This will open `http://localhost:8000` in your browser automatically.

### How it works

On startup, `serve_animation.py`:

1. Reads `tracks_T3.csv` and compiles it into a frame-indexed JSON structure — each frame maps to a list of `[fish_id, x, y]` triplets
2. Embeds that JSON directly into a self-contained HTML page held in memory
3. Starts a minimal HTTP server (Python's built-in `http.server`) on port 8000 and opens the browser

The animation runs entirely in the browser using the Canvas API — no libraries, no framework. Each frame, the script looks up the preloaded JSON for that frame index, updates each fish's position history, and redraws the canvas.

### What you see

- **Tank outline** — the bounding box of the camera frame, with a pixel-coordinate grid for spatial reference
- **10 fish** rendered as colour-coded ellipses, each oriented in its current direction of travel based on the vector from its previous position
- **Fading tails** — each fish leaves a trail whose opacity and width increase toward the present, making direction of movement readable at a glance
- **Fish IDs** — each fish is labelled with its numeric identity (0–9), consistent with the `IDENTITY` column in the CSV
- **Progress bar** — runs along the bottom of the tank, showing position within the trial

### Controls

| Control          | Description                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| **Play / Pause** | Toggle animation                                                                                        |
| **Speed**        | Frames per second (1–20). Higher values scrub through the trial faster                                  |
| **Tail**         | How many historical positions to retain per fish (1–80 frames). Longer tails show more movement history |
| **Scrub**        | Jump to any frame manually. Dragging this resets all tails                                              |

---

## Notes

- The coordinate system is the raw pixel space from the overhead camera. The physical tank is 108 × 54.6 cm; no pixel-to-cm calibration is applied.
- Feeder and LED positions are not encoded in the tracking CSV and are not shown in the visualiser. To add them, identify their pixel coordinates from the original video footage.
- Fish 8 and 9 have the lowest detection coverage (~84% and ~84% of frames respectively) and will occasionally disappear mid-animation — this reflects real gaps in the tracking data, not a bug.
- The animation uses every frame from the CSV (no subsampling), so playback at low speed settings shows the true temporal resolution of the tracking system.
