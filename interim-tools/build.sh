#!/bin/bash

# This shabby script is supposed to hold us over for Q1 2013 while we spin up persona
# in AWS. During that time this should enable jrgm to do build his own packages for staging deploys

# This script assumes you're running it from the r6.build.mtv1.svc.mozilla.com build machine

package=$1
train=$2
code_rev=$3
locale_rev=$4

if [ -z "$package" -o -z "$train" ]; then
  echo "$0 PACKAGE TRAIN [CODE_REV] [LOCALE_REV]"
  echo "$0 browserid train-2013.02.01 7a2f1e479a279246316a1ed5d23fe1c507c35b8e"
  echo "$0 browserid-bigtent train-2013.02.01 7a2f1e479a279246316a1ed5d23fe1c507c35b8e"
  exit 1
fi

if [ "$package" = "browserid" -o "$package" = "browserid_private" ]; then
  rpmname="browserid-server"
elif [ "$package" = "browserid-bigtent" ]; then
  rpmname="browserid-bigtent"
else
  echo "Package \"$package\" not recognized. Aborting..."
  exit 1
fi

if [ ! -e ~/workspace/$package/.git ]; then
  mkdir -p ~/workspace
  git clone https://github.com/mozilla/$package ~/workspace/$package
fi

if [ ! -e ~/workspace/$package/locale ]; then
  cd ~/workspace/$package
  svn co http://svn.mozilla.org/projects/l10n-misc/trunk/browserid/locale
fi

cd ~/workspace/$package
git pull
git checkout $train
if [ "$package" = "browserid" ]; then
  if [ "$locale_rev" ]; then
    svn up -r $locale_rev locale
  else
    svn up locale
  fi
fi

if [ -n "$code_rev" -a "`git rev-parse HEAD`" != "$code_rev" ]; then
  echo "Required code_rev of $code_rev doesn't match current HEAD of `git rev-parse HEAD`. Aborting..."
  exit 1
fi

if make rpm; then
  echo "Success, next you'll need to distribute the RPM"
else
  echo "Build failed. Aborting..."
  exit 1
fi

rm -rf /tmp/.npm
