docker run --rm -it --platform=linux/amd64 \
  --user root \
  -e DISPLAY=host.docker.internal:0 \
  -v /Users/alexandertuna/Downloads/cms/muoncollider/detector-simulation:/home/mucoll/detector-simulation \
  -v /tmp:/tmp \
  ghcr.io/muoncollidersoft/mucoll-sim-alma9:v2.9.8-amd64

#  -p 8800-8899:8800-8899 \

#  -e QT_X11_NO_MITSHM=1 \
#  -e LIBGL_ALWAYS_INDIRECT=1 \



# docker run --rm -it \
#   -e DISPLAY=$DISPLAY \
#   -v /tmp/.X11-unix:/tmp/.X11-unix \
#   -v /Users/alexandertuna/Downloads/cms/muoncollider/detector-simulation:/home/mucoll/detector-simulation \
#   ghcr.io/muoncollidersoft/mucoll-sim-alma9:v2.9.8-amd64



# xauth add $(xauth -f ~/.Xauthority list | tail -n1)
# docker run --rm -it --platform=linux/amd64 \
#   -e DISPLAY=host.docker.internal:0 \
#   -e XAUTHORITY=/tmp/.Xauthority \
#   -v $HOME/.Xauthority:/tmp/.Xauthority:ro \
#   -v /Users/alexandertuna/Downloads/cms/muoncollider/detector-simulation:/home/mucoll/detector-simulation \
#   ghcr.io/muoncollidersoft/mucoll-sim-alma9:v2.9.8-amd64
