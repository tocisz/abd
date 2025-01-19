7zz x $1.7z
./tosvg.py $1
rm -rf $1
mv $1-svg $1
./topdfsvg.py $1
rm -rf $1
