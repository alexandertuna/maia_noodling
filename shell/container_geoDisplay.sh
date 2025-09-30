#
# Run this within a xterm terminal from XQuartz
# Before running this, make sure:
#   XQuartz -> Security -> Allow connections from network clients
#   Run `xhost + 127.0.0.1` from xterm
#
CODE=/Users/alexandertuna/Downloads/cms/muoncollider

docker run --rm -it --platform=linux/amd64 \
  --user root \
  -e DISPLAY=host.docker.internal:0 \
  -v ${CODE}/maia_noodling:/home/mucoll/maia_noodling \
  -v ${CODE}/detector-simulation:/home/mucoll/detector-simulation \
  ghcr.io/muoncollidersoft/mucoll-sim-alma9:v2.9.8-amd64

