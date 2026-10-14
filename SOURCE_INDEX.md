# Recovered source index

Paths below are relative to recovered/work/. These are historical source files;
the list is a provenance index, not a verified build order.

| Area | Files |
| --- | --- |
| Initial prototype | core.c, factory.S, build_mod.py, link_core.py, link_factory.py |
| EmoteWheel Sage dispatcher | d07/build.py, d07/dispatcher.s, d08/build.py, d08/dispatcher.s |
| Mounted adapter | d10/mounted.c, d10/link.py, d10/build.py |
| Supplied fixed D10 baseline | d11/baseline.py; full preferred source not recovered |
| Horse utility | d11/horse.c, d11/link_horse.py, d11/patch_horse.py |
| Memory utility | d12/memory.c, d12/link.py, d12/prepare.py |
| Pause-reason-1 eligibility | d13/cull.c, d13/link.py, d13/finish.py |
| Equipment Sleep | d14/sleep.c, d14/link.py |
| Actual-state Sleep/Awaken toggle | d15/toggle.c, d15/link.py |
| Stale mounted-state repair | d16/build.py |
| Memory input auto-skip | d17/autoskip.c, d17/link.py; superseded by d18/autoskip.c and d18/link.py |
| Final runtime timing | d19/build.py, d21/build.py |
| Native icon generation | d22/build.py, d23/build.py |
| Final icon sizing | d24/build.py through d28/build.py |
| Configuration | ../../config/emotes.json, ../../config/wheel.json |

Existing host test source is retained. Historical verification outputs are not
new test results for this publication. No gameplay changes were made here.
