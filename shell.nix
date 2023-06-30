{ pkgs ? import <nix-unstable> { } }:

with pkgs;
mkShell {
  packages = [ python311 ] ++ (with python311.pkgs; [
    boto3
    openai
    flask
    flask-cors
    flask-jwt-extended
    psycopg
  ]);
  shellHook = ''
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
