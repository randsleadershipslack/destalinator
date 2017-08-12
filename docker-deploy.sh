#!/bin/sh

docker login -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD";
docker build -t randsleadershipslack/destalinator .;
docker tag randsleadershipslack/destalinator randsleadershipslack/destalinator:$TRAVIS_TAG;
docker push randsleadershipslack/destalinator:latest;
docker push randsleadershipslack/destalinator:$TRAVIS_TAG;
