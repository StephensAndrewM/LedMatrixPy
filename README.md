# Andrew's LED Matrix

To install (relative to this project directory):

```bash
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

pip install -r requirements.txt
```

Sample commands:

Development:

* Generate static images of slides defined in config.json: `python3 main.py --generate_images`
* Run show interactively without ending, but don't try to write to hardware: `python3 main.py --fake_display`

`--debug_log` flag can be added for significantly more output.

Testing:

* Run unit tests: `python3 -m unittest`
* Accept new goldens produced by unit tests and delete temp files: `test/accept_goldens.sh`

Weather icons from [DHole](https://github.com/Dhole/weather-pixel-icons)
