# for python3
pushd ./build/html/
python3 -m http.server 3000 --bind 0.0.0.0
popd
