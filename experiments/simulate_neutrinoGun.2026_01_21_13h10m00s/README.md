Simulate tracker hits with BIB and nothing more (neutrino)

Edit steer_reco.py by hand to use a bigger time window for BIB overlay: -4ns to +4ns

Use uncompressed output of slcio file writer (compressionLevel=0) to avoid zlib error for large files

Run locally like:

```
for it in $(seq 0 9); do time ./digitize_neutrinos.sh ${it}; done
```

Diff:

```
 git diff steer_reco.py
diff --git a/k4Reco/steer_reco.py b/k4Reco/steer_reco.py
index 9503359..ebf859e 100644
--- a/k4Reco/steer_reco.py
+++ b/k4Reco/steer_reco.py
@@ -879,10 +882,14 @@ OverlayMIX.Parameters = {
     "Collection_IntegrationTimes": [
         "VertexBarrelCollection", "-0.18", "0.18",
         "VertexEndcapCollection", "-0.18", "0.18",
-        "InnerTrackerBarrelCollection", "-0.36", "0.36",
-        "InnerTrackerEndcapCollection", "-0.36", "0.36",
-        "OuterTrackerBarrelCollection", "-0.36", "0.36",
-        "OuterTrackerEndcapCollection", "-0.36", "0.36",
+        # "InnerTrackerBarrelCollection", "-0.36", "0.36",
+        # "InnerTrackerEndcapCollection", "-0.36", "0.36",
+        # "OuterTrackerBarrelCollection", "-0.36", "0.36",
+        # "OuterTrackerEndcapCollection", "-0.36", "0.36",
+        "InnerTrackerBarrelCollection", "-4.0", "4.0",
+        "InnerTrackerEndcapCollection", "-4.0", "4.0",
+        "OuterTrackerBarrelCollection", "-4.0", "4.0",
+        "OuterTrackerEndcapCollection", "-4.0", "4.0",
         "ECalBarrelCollection", "-0.5", "15.",
         "ECalEndcapCollection", "-0.5", "15.",
         "HCalBarrelCollection", "-0.5", "15.",
```
