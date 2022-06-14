To install (relative to this project):

mkdir bindings
cd bindings
git clone https://github.com/hzeller/rpi-rgb-led-matrix
cd rpi-rgb-led-matrix
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
