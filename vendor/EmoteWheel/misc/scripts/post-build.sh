#!/bin/bash
set -eu
mkdir -p deploy
cp -- ./stage.nso ./deploy/subsdk4
cp -- ./stage.npdm ./deploy/main.npdm
