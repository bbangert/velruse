from flask import (
    Flask,
)

from velruse.wsgi import make_app

from werkzeug.wsgi import DispatcherMiddleware


app = Flask(__name__)
app.config.from_envvar('FLASK_SETTINGS')

@app.route('/login')
def login_view(request):
    pass

@app.route('/login/callback')
def login_callback_view(request):
    pass

velruse = make_app({}, **app.config['VELRUSE'])

application = DispatcherMiddleware(app, {
    '/velruse': velruse,
})

if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    run_simple('0.0.0.0', port, application, use_reloader=True)
