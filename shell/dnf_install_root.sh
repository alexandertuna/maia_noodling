#
# Run as root user within a muoncollider docker image
#   Then do `su mucoll` to enjoy the fruits of your labor
#
dnf install -y \
    firefox \
    xdg-utils \
    glx-utils \
    mesa-dri-drivers \
    mesa-libGLU \
    mesa-libOSMesa \
    mesa-demos \
    freeglut \
    libX11 \
    libXext \
    libXrender \
    libXft \
    libXi \
    libXmu \
    xorg-x11-xauth \
    xorg-x11-utils
