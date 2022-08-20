To install (relative to this project directory):

```
mkdir bindings
cd bindings
git clone https://github.com/hzeller/rpi-rgb-led-matrix
cd rpi-rgb-led-matrix
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
sudo apt install python3-pil
sudo apt install libopenjp2-7
mkdir debug
chmod 777 debug
```

Weather icons from https://github.com/Dhole/weather-pixel-icons