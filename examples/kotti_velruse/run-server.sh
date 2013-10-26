#/bin/bash

# make sure proxy settings are ignored
`env | fgrep -i _proxy | cut -d= -f1 | xargs echo unset`

if [ ! -d kotti_velruse/openid-selector ] ;then
  which git
  if [ $? -ne 0 ] ; then
    sudo apt-get install git -y
  fi
  pushd kotti_velruse
  git clone https://github.com/frgomes/openid-selector.git
  popd
fi

pserve development.ini --reload
