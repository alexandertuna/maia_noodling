Geometry: v04, equally-spaced OT layers

Simulate tracker hits with BIB and nothing more (neutrino)

Edit steer_reco.py by hand to use a bigger time window for BIB overlay (-5 to +15ns), drop calorimeter sim and digi collections, and drop tracker digi collections

Run locally like:

```
for it in $(seq 0 9); do time ./digitize_neutrinos.sh ${it}; done
```

Diff:

```
diff --git a/k4Reco/steer_reco.py b/k4Reco/steer_reco.py
index 9503359..25e9701 100644
--- a/k4Reco/steer_reco.py
+++ b/k4Reco/steer_reco.py
@@ -14,6 +14,7 @@ parser.add_argument("--TypeEvent", type=str, default="electronGun_pT_0_50", help
 parser.add_argument("--InFileName", type=str, default="0", help="Input file name for the simulation")
 parser.add_argument("--code", type=str, default="/code", help="Top-level directory for code")
 parser.add_argument("--data", type=str, default="/dataMuC", help="Top-level directory for data")
+parser.add_argument("--compressionLevel", type=int, default=None, help="Set compression level of output")
 parser.add_argument("--skipReco", action="store_true", default=False, help="Skip reconstruction")
 parser.add_argument("--skipTrackerConing", action="store_true", default=False, help="Skip tracker coning")
 the_args = parser.parse_args()
@@ -68,12 +69,6 @@ else:
             "LCRelation"
         ],
         "DropCollectionNames": [
-            "AllTracks", "SeedTracks", "SiTracks",
-            "MCPhysicsParticles", "MCPhysicsParticles_IP"
-        ],
-        "FullSubsetCollections": [
-            "EcalBarrelCollectionSel", "EcalEndcapCollectionSel",
-            "HcalBarrelCollectionSel", "HcalEndcapCollectionSel",
             f"IBTrackerHits{Coned}", f"IETrackerHits{Coned}",
             f"OBTrackerHits{Coned}", f"OETrackerHits{Coned}",
             f"VBTrackerHits{Coned}", f"VETrackerHits{Coned}",
@@ -81,27 +76,44 @@ else:
             f"IBTrackerHitsRelations{Coned}", f"IETrackerHitsRelations{Coned}",
             f"OBTrackerHitsRelations{Coned}", f"OETrackerHitsRelations{Coned}",
             f"VertexBarrelCollection{Coned}", f"VertexEndcapCollection{Coned}",
-            f"InnerTrackerBarrelCollection{Coned}", f"InnerTrackerEndcapCollection{Coned}",
-            f"OuterTrackerBarrelCollection{Coned}", f"OuterTrackerEndcapCollection{Coned}",
+            f"InnerTrackerEndcapCollection{Coned}",
+            f"OuterTrackerEndcapCollection{Coned}",
+            "AllTracks", "SeedTracks", "SiTracks",
+            "MCPhysicsParticles", "MCPhysicsParticles_IP"
+        ],
+        "FullSubsetCollections": [
+            "EcalBarrelCollectionSel", "EcalEndcapCollectionSel",
+            "HcalBarrelCollectionSel", "HcalEndcapCollectionSel",
+            # f"IBTrackerHits{Coned}", f"IETrackerHits{Coned}",
+            # f"OBTrackerHits{Coned}", f"OETrackerHits{Coned}",
+            # f"VBTrackerHits{Coned}", f"VETrackerHits{Coned}",
+            # f"VBTrackerHitsRelations{Coned}", f"VETrackerHitsRelations{Coned}",
+            # f"IBTrackerHitsRelations{Coned}", f"IETrackerHitsRelations{Coned}",
+            # f"OBTrackerHitsRelations{Coned}", f"OETrackerHitsRelations{Coned}",
+            # f"VertexBarrelCollection{Coned}", f"VertexEndcapCollection{Coned}",
+            f"InnerTrackerBarrelCollection{Coned}", # f"InnerTrackerEndcapCollection{Coned}",
+            f"OuterTrackerBarrelCollection{Coned}", # f"OuterTrackerEndcapCollection{Coned}",
             "SiTracks_Refitted"
         ],
         "KeepCollectionNames": [
             "EcalBarrelCollectionSel", "EcalEndcapCollectionSel",
             "HcalBarrelCollectionSel", "HcalEndcapCollectionSel",
-            f"IBTrackerHits{Coned}", f"IETrackerHits{Coned}",
-            f"OBTrackerHits{Coned}", f"OETrackerHits{Coned}",
-            f"VBTrackerHits{Coned}", f"VETrackerHits{Coned}",
-            f"VBTrackerHitsRelations{Coned}", f"VETrackerHitsRelations{Coned}",
-            f"IBTrackerHitsRelations{Coned}", f"IETrackerHitsRelations{Coned}",
-            f"OBTrackerHitsRelations{Coned}", f"OETrackerHitsRelations{Coned}",
-            f"VertexBarrelCollection{Coned}", f"VertexEndcapCollection{Coned}",
-            f"InnerTrackerBarrelCollection{Coned}", f"InnerTrackerEndcapCollection{Coned}",
-            f"OuterTrackerBarrelCollection{Coned}", f"OuterTrackerEndcapCollection{Coned}",
+            # f"IBTrackerHits{Coned}", f"IETrackerHits{Coned}",
+            # f"OBTrackerHits{Coned}", f"OETrackerHits{Coned}",
+            # f"VBTrackerHits{Coned}", f"VETrackerHits{Coned}",
+            # f"VBTrackerHitsRelations{Coned}", f"VETrackerHitsRelations{Coned}",
+            # f"IBTrackerHitsRelations{Coned}", f"IETrackerHitsRelations{Coned}",
+            # f"OBTrackerHitsRelations{Coned}", f"OETrackerHitsRelations{Coned}",
+            # f"VertexBarrelCollection{Coned}", f"VertexEndcapCollection{Coned}",
+            f"InnerTrackerBarrelCollection{Coned}", # f"InnerTrackerEndcapCollection{Coned}",
+            f"OuterTrackerBarrelCollection{Coned}", # f"OuterTrackerEndcapCollection{Coned}",
             "SiTracks_Refitted", "MCParticle_SiTracks_Refitted"
         ],
         "LCIOOutputFile": [f"{the_args.data}/recoBIB/{the_args.TypeEvent}/{the_args.TypeEvent}_reco_{the_args.InFileName}.slcio"],
         "LCIOWriteMode": ["WRITE_NEW"]
     }
+if the_args.compressionLevel is not None:
+    Output_REC.Parameters["CompressionLevel"] = [str(the_args.compressionLevel)]
 
 InitDD4hep = MarlinProcessorWrapper("InitDD4hep")
 InitDD4hep.OutputLevel = INFO
@@ -879,10 +891,14 @@ OverlayMIX.Parameters = {
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
+        "InnerTrackerBarrelCollection", "-5.0", "15.0",
+        "InnerTrackerEndcapCollection", "-5.0", "15.0",
+        "OuterTrackerBarrelCollection", "-5.0", "15.0",
+        "OuterTrackerEndcapCollection", "-5.0", "15.0",
         "ECalBarrelCollection", "-0.5", "15.",
         "ECalEndcapCollection", "-0.5", "15.",
         "HCalBarrelCollection", "-0.5", "15.",
```
