    export LDFLAGS="-L/usr/local/opt/openssl/lib"
    export CPPFLAGS="-I/usr/local/opt/openssl/include"
    export PKG_CONFIG_PATH="/usr/local/opt/openssl/lib/pkgconfig"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin/python3:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
