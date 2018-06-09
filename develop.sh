PREVVER="6.3.7"
PREVCODE="78"
CURVER="6.3.8"
CURCODE="79"

#
# Check if smali patch can be reused.
#
compare(){
    if [[ `(diff -rq src-v$1/smali/jp/radiko/ src-v$2/smali/jp/radiko/|grep -v '^Only in' |awk '{print $2}'| cut -d '/' -f 2- ;cat patch/$1/smali.patch|grep diff|grep smali/jp |awk '{print $3}' |cut -d '/' -f 2- ) |uniq -d` == "" ]] ;then
        echo "Patch for $1 is suitable for $2"
    else
        echo "Something changed in files which should be patched, we cannot continue. Details:"
        echo `(diff -rq src-v$1/smali/jp/radiko/ src-v$2/smali/jp/radiko/|grep -v '^Only in' |awk '{print $2}'| cut -d '/' -f 2- ;cat patch/$1/smali.patch|grep diff|grep smali/jp |awk '{print $3}' |cut -d '/' -f 2- ) |uniq -d`
    fi
}
downloadRadiko(){
        echo "Downloading radiko original apk"
        DOWNLOADLINK=`curl -s  https://apkpure.com/radiko-jp-for-android/jp.radiko.Player/download/$1-APK  |grep -oP "(?<=id=\"iframe_download\" src=\").*?(?=\")"`
        if [ $DOWNLOADLINK ];then
            wget -O src-v$2.apk  $DOWNLOADLINK || exit 1
        else
            exit 1
        fi
}

downloadRadiko $PREVCODE $PREVVER
downloadRadiko $CURCODE $CURVER
java -jar tool/apktool_2.3.2.jar d -f src-v$PREVVER.apk 
java -jar tool/apktool_2.3.2.jar d -f src-v$CURVER.apk
compare $PREVVER $CURVER


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

