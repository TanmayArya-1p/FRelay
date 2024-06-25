## Setup
- Install Docker
- ```git clone https://github.com/TanmayArya-1p/FRelay.git```

## Run
- ```docker build -t <image_name> .```
- ```docker run -d --name <container_name> -p <image_name>```

- Configure the Master Key(Default: `123`) in config.ini
- Server Runs at Port 3000 By Default (To Change this just change the port number in the Dockerfile)  
- Simulate Requests Through `/simulate`
