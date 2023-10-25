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
sudo apt install ntpdate
mkdir debug
chmod 777 debug

cd ~/Downloads
wget https://github.com/protocolbuffers/protobuf/releases/download/v24.4/protoc-24.4-linux-x86_64.zip
sudo unzip -o protoc-24.4-linux-x86_64.zip -d /usr/local bin/protoc 
sudo unzip -o protoc-24.4-linux-x86_64.zip -d /usr/local "include/*"
protoc -I=transit/gtfs-realtime/proto/ transit/gtfs-realtime/proto/gtfs-realtime.proto --python_out=.
```

Weather icons from https://github.com/Dhole/weather-pixel-icons