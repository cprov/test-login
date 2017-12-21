# Autentication test project

This project is here to test how to use Ubuntu Openid and Snap store macaroon.
You need Python3 to run the project:

```bash
# Run the project
pip install -r requirements.txt
python app.py
```

# Documentation
* [Macaroon API ](https://dashboard.snapcraft.io/docs/api/macaroon.html)
* [Flask Openid](https://pythonhosted.org/Flask-OpenID/)
* [Source of inspiration for Openid](https://github.com/mitsuhiko/flask-openid/blob/master/example/example.py)


## On Mac

```bash
$ brew install python3 nacl libsodium
$ pip3 install virtualenv
$ virtualenv -p python3 env
$ . env/bin/active
$ pip install -r requirements.txt
$ python app.py
```


