cd zuul/doc/source/examples
docker-compose up -d

cd ../../../..

python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

./.venv/bin/python create_repo.py conan-repo
./.venv/bin/python create_repo.py zuul-config
