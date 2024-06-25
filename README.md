## Setup

####
    git clone https://github.com/TanmayArya-1p/FRelay.git
    
- Configure the Master Key(Default: `123`) in [config.ini](https://github.com/TanmayArya-1p/FRelay/blob/main/api/config.ini)
- Server Runs at Port 3000 By Default (To Change this just change the port number in the Dockerfile)

## Run

- Build Docker Image:
####
    docker build -t <image_name> .

- Run Created Image in a Container:
#### 
    docker run -d --name <container_name> -p <image_name>


- Simulate Requests Through `/simulate`
