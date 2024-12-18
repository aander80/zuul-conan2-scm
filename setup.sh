cd zuul
git apply ../zuul-submodule.patch || true

cd doc/source/examples
docker-compose up -d

cd ../../../..

python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

echo Waiting for Gerrit to start...

while true
do
    sleep 1

    http_code=$(curl --verbose -s -o /tmp/result.txt -w '%{http_code}' "http://localhost:8080/config/server/version";)

    if [ "$http_code" -eq 200 ]; then
        echo "Gerrit started"
        break
    fi
done

./.venv/bin/python create_repo.py conan-repo
./.venv/bin/python create_repo.py zuul-config

docker exec -it examples_scheduler_1 zuul-scheduler full-reconfigure
