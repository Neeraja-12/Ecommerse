echo "BUILD START"
python -m pip install -r ecommerce/requirements.txt
python ecommerce/manage.py collectstatic --noinput --clear
echo "BUILD END"