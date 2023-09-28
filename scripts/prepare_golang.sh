#!/bin/bash

set -ex

GO_VERSION=1.21.1
ARCH=$(uname -m)
OS=linux

if [ $ARCH == "x86_64" ]; then
  go_arch=amd64
elif [ $ARCH == "arm64" ]; then
  go_arch=arm64
elif [ $ARCH == "i686" ]; then
  go_arch=386
else
  echo "unknown arch=${ARCH}"
  exit 1
fi


FILENAME=go${GO_VERSION}.${OS}-${go_arch}.tar.gz
echo $FILENAME

curl -sS -LO https://go.dev/dl/${FILENAME}
tar -C /usr/local -xzf $FILENAME
export PATH=$PATH:/usr/local/go/bin
go version
