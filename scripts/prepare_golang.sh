#!/bin/bash

set -ex

GO_VERSION=1.21.1
ARCH=$(uname -m)
OS=Linux

if [ $ARCH == "x86_64" ]; then
  go_arch=amd64
elif [ $ARCH == "arm64" ]; then
  go_arch=arm64
else
  echo "unknown arch=${ARCH}"
  exit 1
fi

DOWNLOAD="https://go.dev/dl/go1.21.1.darwin-${go_arch}.pkg"

echo $DOWNLOAD

FILENAME=go${GO_VERSION}.${OS}-${ARCH}.tar.gz
curl -sS -LO https://go.dev/dl/${FILENAME}
tar -C /usr/local -xzf $FILENAME
export PATH=$PATH:/usr/local/go/bin
go version
