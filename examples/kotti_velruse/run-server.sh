#/bin/bash

# make sure proxy settings are ignored
`env | fgrep -i _proxy | cut -d= -f1 | xargs echo unset`

if [ ! -d kotti_velruse/openid-selector ] ;then
  if [ -d ~/sources/frgomes/openid-selector/master/openid-selector ] ;then
    ln -s ~/sources/frgomes/openid-selector/master/openid-selector kotti_velruse/openid-selector
  else
    which git
    if [ $? -ne 0 ] ; then
      sudo apt-get install git -y
    fi
    pushd kotti_velruse
    git clone https://github.com/frgomes/openid-selector.git
    popd
  fi
fi

pserve development.ini --reload
