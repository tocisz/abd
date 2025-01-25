7zz x $1.7z
./make_font.py $1
rm -rf $1
mv $1-svg $1
./deduplicate2.py $1 $1-svg $1
rm -rf $1
mv $1-svg $1
./svg2pdf2.py $1
rm -rf $1
