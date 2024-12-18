#!/bin/bash

cd zuul
git apply ../zuul-submodule.patch || true
cd ..

docker compose --project-directory zuul/doc/source/examples up -d

python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

echo Waiting for Gerrit to start...

while true
do
    http_code=$(curl --verbose -s -o /tmp/result.txt -w '%{http_code}' "http://localhost:8080/config/server/version";)

    if [ "$http_code" -eq 200 ]; then
        echo "Gerrit started"
        break
    fi

    sleep 1
done

echo Waiting for gerritconfig service to finish...

while true
do
    gerritconfig_status=$(docker compose --project-directory zuul/doc/source/examples ps -a gerritconfig --format "{{.Status}}";)

    if [[ $gerritconfig_status =~ "Exited" ]]; then
        echo "gerritconfig service finished"
        break
    fi

    sleep 1
done

./.venv/bin/python ./create_repo.py conan-repo
./.venv/bin/python ./create_repo.py zuul-config

docker exec -it examples-scheduler-1 zuul-scheduler full-reconfigure
