python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

grep -v '^nersc-pymon==' requirements.txt > requirements_local.txt
python -m pip install -r requirements_local.txt

cd ~/MAGENT

conda deactivate
source .venv/bin/activate

python -m pip install --upgrade pip
grep -v '^nersc-pymon==' requirements.txt > requirements_local.txt
python -m pip install -r requirements_local.txt
python -m pip install fastmcp mcp aiofiles

cp -n .env.template .env
chmod 600 .env
mkdir -p cache

python -u doe_metrics_client.py

