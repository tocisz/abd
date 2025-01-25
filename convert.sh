7zz x $1.7z
./png2svg.py $1
rm -rf $1
mv $1-svg $1
./svg2pdf.py $1
rm -rf $1
