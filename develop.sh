PREVVER="6.3.6"
CURVER="6.3.7"

#
# Check if smali patch can be reused.
#
if [[ `{diff -rq src-v$PREVVER/smali/jp/radiko/ src-v$CURVER/smali/jp/radiko/|awk '{print $2}'| cut -d '/' -f 2- ;cat ../patch/$PREVVER/smali.patch|grep diff|grep smali/jp |awk '{print $3}' |cut -d '/' -f 2- } |uniq -d` == "" ]] ;then
    echo "Patch for $PREVVER is suitable for $CURVER"
else
    echo "Something changed in files which should be patched, we cannot continue. Details:"
    echo `{diff -rq src-v$PREVVER/smali/jp/radiko/ src-v$CURVER/smali/jp/radiko/|awk '{print $2}'| cut -d '/' -f 2- ;cat ../patch/$PREVVER/smali.patch|grep diff|grep smali/jp |awk '{print $3}' |cut -d '/' -f 2- } |uniq -d`
fi

#
# Try generate so patch automatic
#
# [Not Implemented]

function work(){
    for file in `ls $1`   
        do
            if [ -d $1"/"$file ] ;then
                work $1"/"$file
            else
                echo "work on $1/$file"
                python parser.py $1"/"$file 
            fi
        done
} 

#work $1
#git diff --binary 
#then change patch to  a/lib b/lib

