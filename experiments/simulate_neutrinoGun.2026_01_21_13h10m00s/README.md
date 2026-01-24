Simulate tracker hits with BIB and nothing more (neutrino)

Edit steer_reco.py by hand to use a bigger time window for BIB overlay: -4ns to +4ns

Use uncompressed output of slcio file writer (compressionLevel=0) to avoid zlib error for large files

Run locally like:

```
for it in $(seq 0 9); do time ./digitize_neutrinos.sh ${it}; done
```
