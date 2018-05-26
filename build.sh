VERSIONCODE="78"
VERSIONNAME="6.3.7"
VERSIONSHA1="f20860ec42ef8e8fa0e80bdfebd07239acda52ba"
CURDIR=`pwd`
MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script is in the" $MYDIR
BUILDTOOLDIR=$MYDIR/tool
#
# 77 -> 6.3.6 03145e09e79d72cf27ea00437f1c872cae858b78
# 78 -> 6.3.7 f20860ec42ef8e8fa0e80bdfebd07239acda52ba
#
#
# if stable use latest valid version
# else check update first if update available :  use parser to generate so.patch and use previous version smali.patch if specified file not changed.
#
downloadRadiko(){
    echo "Downloading radiko original apk"
    DOWNLOADLINK=`curl -s  https://apkpure.com/radiko-jp-for-android/jp.radiko.Player/download/$VERSIONCODE-APK  |grep -oP "(?<=id=\"iframe_download\" src=\").*?(?=\")"`
    if [ $DOWNLOADLINK ];then
        wget -O $BUILDTOOLDIR/src-v$VERSIONNAME.apk  $DOWNLOADLINK || exit 1
    else
        exit 1
    fi
}

downloadApktool(){
    echo "Downloading Apktool"
    wget -O $BUILDTOOLDIR/apktool_2.3.2.jar https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.3.2.jar || exit 1
}


echo "Using " $BUILDTOOLDIR " for apktool and radiko original android apk"
if [ ! -x "$BUILDTOOLDIR" ];then
    mkdir $BUILDTOOLDIR
    downloadRadiko
    downloadApktool
else
    if [[ ! -f $BUILDTOOLDIR/src-v$VERSIONNAME.apk ]] || [[ `md5sum $BUILDTOOLDIR/src-v$VERSIONNAME.apk |awk '{print $1}'` != $VERSIONSHA1  ]] ;then
        downloadRadiko
    fi
    if [[ ! -f $BUILDTOOLDIR/apktool_2.3.2.jar ]] || [[  `md5sum $BUILDTOOLDIR/apktool_2.3.2.jar |awk '{print $1}'` !=  '953ed8a553becac4e713d1073912f15f' ]];then
        downloadApktool
    fi
fi

BUILDDIR=`mktemp -d`
echo "Create tmp build directory" $BUILDDIR
echo "Decompiling"
java -jar $BUILDTOOLDIR/apktool_2.3.2.jar d $BUILDTOOLDIR/src-v$VERSIONNAME.apk -f -o $BUILDDIR
cd $BUILDDIR 
echo "Applying patch from " $MYDIR/patch/$VERSIONNAME/smali.patch
git apply --stat $MYDIR/patch/$VERSIONNAME/smali.patch
git apply $MYDIR/patch/$VERSIONNAME/smali.patch
#if debug , generate so.patch from parser.py
#
echo "Applying patch from " $MYDIR/patch/$VERSIONNAME/so.patch
git apply --stat $MYDIR/patch/$VERSIONNAME/so.patch
git apply $MYDIR/patch/$VERSIONNAME/so.patch
echo "Compiling && Packaging && Signing"
java -jar $BUILDTOOLDIR/apktool_2.3.2.jar b $BUILDDIR
cd $BUILDDIR/dist && keytool -genkey -keystore fake.jks -keyalg RSA -keysize 2048 -alias fake  -storepass 123456 -dname "CN=fake" -keypass 123456  -validity 36500 && jarsigner -keystore fake.jks -digestalg SHA1 -sigalg SHA1withRSA -storepass 123456 -signedjar $MYDIR/radiko_kai_$VERSIONNAME.apk src-v$VERSIONNAME.apk fake 
echo "Removing tmp directory" $BUILDDIR
rm -r $BUILDDIR
echo "Result is " $MYDIR/radiko_kai_$VERSIONNAME.apk
cd $CURDIR
