# Neuro-Flow

Neuro-Flow started as a team design project for the System Design and Engineering Thinking+ short course in Cambridge. The team presented the concept on 12 February 2026. The independent follow-up includes an interactive replay prototype and a preliminary offline analysis dated 9 November 2026.

## Course project and credit

The original team slides are retained privately in the project workspace and are not distributed in the source archive. The title slide credits Zhang Xu, Fan Xiaole, Huang Ziyang, Xu Jiantao, Liu Xinzhu, Yang Hanrui, and Long Siyu. Slides 18–23 cover the system architecture and interaction flow, with Fan Xiaole credited on the presentation slides for the rich picture and flow diagram. The team also analyzed risks with FMEA and used a bow-tie diagram to identify controls around potential privacy leakage.

Michael Sutcliffe and James Ward provided guidance during the February in-person team project, according to Fan Xiaole. The follow-up was independent. The prototype and offline analysis are dated by their actual implementation and evaluation.

## Interactive prototype

Open [demo.html](demo.html) in a desktop browser. It runs locally with no package dependencies, network requests, or persistence.

1. Keep **Learn** selected. Turn on **Use simulated signal** and play **Early friction, later recovery**. The model applies a bounded engineering-topic boost after two three-window segments show enough recovery.
2. Click **No** under the feedback question to override the signal, then click **Clear**. Turn the signal off to see the goal-based order return.
3. Replay **Signal dropout** to see the policy drop the boost when data go missing. Replay **Low-quality spike** to see why a large apparent change can leave the order intact. Switch to **Relax** to see the effect of a different explicit viewing goal.

The engagement baseline sorts by a preset score. The two goal-based rankings use the same goal, explicit feedback, catalog, and diversity rule. The last column can also use the simulated cue. Weights, quality scores, thresholds, and catalog attributes were chosen to illustrate these mechanics. The demo replays synthetic proxy values and uses a rule-based ranking.

## Controlled replay

Run the browser policy against six deterministic traces with Node.js:

```sh
node replay.cjs
```

The replay holds the catalog and the Learn goal fixed. The control uses goals and explicit feedback. The two signal conditions apply the same recovery rule, with the quality threshold set to 0.65 or 0. Both require present and finite signal values. Each decision uses only the samples available at that step. The table counts windows in which the top recommendation differs from the control. Explicit feedback is unset for this comparison. The runner separately verifies that opt-out and explicit feedback suppress the cue at every step.

| Synthetic trace | Quality gate | No quality threshold |
|---|---:|---:|
| Clean recovery | 7/12 | 7/12 |
| Sustained low response | 0/12 | 0/12 |
| Recovery followed by dropout | 3/12 | 3/12 |
| Spike correctly flagged as low quality | 0/12 | 4/12 |
| Spike incorrectly reported as high quality | 4/12 | 4/12 |
| Clean recovery incorrectly flagged as low quality | 0/12 | 7/12 |

On the clean recovery trace, the first change occurs at simulated second 5. Dropout begins at second 8 and both policies immediately return to the control choice. The quality gate is sensitive to the accuracy of the supplied quality flag. These counts describe ranking behavior on constructed inputs. User-rated value remains a prospective endpoint.

For a prospective evaluation, assign the two goal-based policies in a randomized, counterbalanced crossover. Hold the candidate pool and ranking parameters fixed across the two conditions, obtain a delayed rating of whether each session was worth the participant's time, and analyze paired differences per participant. Record artifact rejection, opt-outs, and topic exposure separately. AMIGOS could support a preliminary evaluation of temporal affect estimates under its [data access agreement](https://www.eecs.qmul.ac.uk/mmv/datasets/amigos/doc/eula.pdf). Its external affect ratings address a different endpoint from user-rated session value.

## Verified offline pilot (10 November 2026)

The alignment audit matches the complete benchmark rows to both metadata and EEG vectors. 91 pairs from participant 01 are verified. The earlier 30-participant result depended on an unverified viewing-order mapping and has been retired from the homepage.

Run the new protocol into a fresh output directory:

```sh
python3 -m pip install -r requirements.txt
python3 evaluate.py --cache /tmp/neuro-flow-cache --output runs/verified
```

The script emits an alignment audit with source hashes and exclusions, a code/environment manifest, explicit train/validation/test assignments, model selection scores, test MAE and per-video held-out predictions. Load `replay.json` in `methods.html` to inspect those predictions. Rows stay in the local browser session. The output directory is local analysis material and should stay outside the public homepage and downloadable source package.

The first 63 clips are development data (47 inner-fit and 16 inner-validation clips), with the last 28 held out. A fixed ridge grid of 0.1, 1, 10 and 100 is selected using inner-validation MAE for each feature set. The selected model is refitted on all 63 development clips. Predictions are clipped to the questionnaire range [1, 5]. This chronological protocol was selected before the new test results were computed.

| Model | Test MAE |
|---|---:|
| Training mean | 1.1457 |
| Behavior | 0.6642 |
| Behavior + EEG band summaries | 0.7229 |
| Behavior + full-channel EEG | 0.9263 |

Both EEG feature sets increase error on this small sample. Full-recording upstream normalization makes this an offline evaluation. One participant and 28 test clips provide limited evidence. The task predicts immersion after viewing, and the user-rated value of a recommendation remains unmeasured.

## References

- [EEG-SVRec paper](https://doi.org/10.1145/3626772.3657890) and [pinned data and preprocessing code](https://github.com/hezy18/EEG-SVRec/tree/5f40c0476bde48d195de55c933293a0849977011).
- [Cambridge Rainbow Group's emotionally intelligent interfaces](https://www.cl.cam.ac.uk/research/rainbow/emotions/), related work on contextual affect inference in interactive systems.
- [Cambridge Cognitive Architecture](https://www.cca.arct.cam.ac.uk/), a related closed-loop design direction using neural and physiological signals for responsive environments.
- [AMIGOS paper](https://eecs.qmul.ac.uk/mmv/datasets/amigos/doc/Paper_TAC.pdf), a candidate for studying longer video trajectories with windowed external affect ratings.
