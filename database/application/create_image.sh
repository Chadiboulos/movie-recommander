#/bin/sh

#build the docker image
sudo docker build -t recofilmsmlopsoct2023/movieflix-initdb:latest .

if [ "$1" == "-p" ]; then
    #push docker loging 
    docker login --username recofilmsmlopsoct2023

    #push docker image
    docker push recofilmsmlopsoct2023/movieflix-initdb:latest
fi

