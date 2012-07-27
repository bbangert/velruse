import requests
from flask import (
    Flask,
    render_template,
    request
)

from velruse.app import make_velruse_app

from werkzeug.wsgi import DispatcherMiddleware

app = Flask(__name__)
app.config.from_envvar('FLASK_SETTINGS')
app.debug = True


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logged_in', methods=['POST'])
def login_callback():
    token = request.form['token']
    payload = {'format': 'json', 'token': token}
    response = requests.get(request.host_url + 'velruse/auth_info', params=payload)
    return render_template('result.html', result=response.json)

velruse = make_velruse_app({}, **app.config['VELRUSE'])

application = DispatcherMiddleware(app, {
    '/velruse': velruse,
})

if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5020))
    run_simple('0.0.0.0', port, application, use_reloader=True, threaded=True)
