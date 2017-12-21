import datetime
import flask
from flask_openid import OpenID
import requests

import authentication
from macaroon import MacaroonRequest, MacaroonResponse


app = flask.Flask(__name__)
app.config.update(
    SECRET_KEY="This is a super secret key!",
    DEBUG=True
)

oid = OpenID(
    app,
    safe_roots=[],
    extension_responses=[MacaroonResponse]
)


def redirect_to_login():
    return flask.redirect(''.join([
        'login?next=',
        flask.request.url_rule.rule,
    ]))


@app.route('/')
def homepage():
    context = {}
    if authentication.is_authenticated(flask.session):
        context['connected'] = True

    return flask.render_template('index.html', **context)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if authentication.is_authenticated(flask.session):
        return flask.redirect(oid.get_next_url())

    root = authentication.request_macaroon()
    openid_macaroon = MacaroonRequest(
        caveat_id=authentication.get_caveat_id(root)
    )
    flask.session['macaroon_root'] = root

    return oid.try_login(
        'https://login.ubuntu.com',
        ask_for=['email', 'nickname'],
        ask_for_optional=['fullname'],
        extensions=[openid_macaroon]
    )


@oid.after_login
def after_login(resp):
    flask.session['openid'] = resp.identity_url
    flask.session['macaroon_discharge'] = resp.extensions['macaroon'].discharge
    return flask.redirect('/account')


@app.route('/account')
def get_account():
    if not authentication.is_authenticated(flask.session):
        return redirect_to_login()

    authorization = authentication.get_authorization_header(
        flask.session['macaroon_root'],
        flask.session['macaroon_discharge']
    )

    headers = {
        'X-Ubuntu-Series': '16',
        'X-Ubuntu-Architecture': 'amd64',
        'Authorization': authorization
    }

    url = 'https://dashboard.snapcraft.io/dev/api/account'
    response = requests.request(url=url, method='GET', headers=headers)

    verified_response = authentication.verify_response(
        response,
        flask.session,
        url,
        '/account',
        '/login'
    )

    if verified_response is not None:
        if verified_response['redirect'] is None:
            response.raise_for_status()
        return flask.redirect(verified_response.redirect)

    context = {
        'account': response.json()
    }

    return flask.render_template('account.html', **context)


@app.route('/snaps/<snap_name>')
def get_snap(snap_name):
    if not authentication.is_authenticated(flask.session):
        return redirect_to_login()

    authorization = authentication.get_authorization_header(
        flask.session['macaroon_root'],
        flask.session['macaroon_discharge']
    )

    headers = {
        'X-Ubuntu-Series': '16',
        'X-Ubuntu-Architecture': 'amd64',
        'Authorization': authorization
    }

    url = 'https://api.snapcraft.io/api/v1/snaps/details/{}'.format(snap_name)
    response = requests.request(url=url, method='GET', headers=headers)
    verified_response = authentication.verify_response(
        response,
        flask.session,
        url,
        '/snaps/{}'.format(snap_name),
        '/login'
    )
    if verified_response is not None:
        if verified_response['redirect'] is None:
            response.raise_for_status()
        return flask.redirect(verified_response.redirect)

    details = response.json()

    snap_id = details['snap_id']
    url = 'https://dashboard.snapcraft.io/dev/api/snaps/metrics'
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    month_ago = yesterday -  datetime.timedelta(days=30)
    data = {
        "filters": [
            {"metric_name": "installed_base_by_channel",
             "snap_id": snap_id,
             "start": month_ago.strftime('%Y-%m-%d'),
             "end": yesterday.strftime('%Y-%m-%d')},
            {"metric_name": "installed_base_by_operating_system",
             "snap_id": snap_id,
             "start": month_ago.strftime('%Y-%m-%d'),
             "end": yesterday.strftime('%Y-%m-%d')},
            {"metric_name": "installed_base_by_version",
             "snap_id": snap_id,
             "start": month_ago.strftime('%Y-%m-%d'),
             "end": yesterday.strftime('%Y-%m-%d')},
        ]
    }
    response = requests.request(url=url, method='POST', json=data, headers=headers)
    metrics = response.json()

    context = {
        'details': details,
        'metrics': metrics,
    }

    return flask.render_template('details.html', **context)


@app.route('/logout')
def logout():
    if authentication.is_authenticated(flask.session):
        authentication.empty_session(flask.session)
    return flask.redirect('/')


if __name__ == '__main__':
    app.run()
