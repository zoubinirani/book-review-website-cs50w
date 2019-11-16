export FLASK_APP=application.py
export FLASK_DEBUG=1
export DATABASE_URL=postgres://kvizzopwfxfbol:f4b96009a5c13113278b3d821e4eeed4d4b89b0fa75e9a19f07d2eb06aea0c54@ec2-174-129-253-180.compute-1.amazonaws.com:5432/d472fmg073t0aa

python3 import.py
flask run

