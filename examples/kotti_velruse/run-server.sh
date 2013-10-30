#/bin/bash


# give a little push to Kotti installation
pip install -r https://raw.github.com/Kotti/Kotti/0.9.2/requirements.txt $PIP_OPTIONS

# installs Kotti and kotti_velruse
python setup.py develop

# uninstall velruse cos rgomes-velruse replaces it for the time being
pip uninstall velruse << EOF
y
EOF

# make sure proxy settings are ignored
`env | fgrep -i _proxy | cut -d= -f1 | xargs echo unset`

# start server
echo .
echo .
echo '*************************************************'
echo '*                                               *'
echo '* Starting the server...                        *'
echo '*                                               *'
echo '* Please visit context /login when it is ready. *'
echo '*                                               *'
echo '*************************************************'
pserve development.ini --reload
