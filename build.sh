CURDIR=`pwd`
MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script is in the" $MYDIR
BUILDTOOLDIR=$MYDIR/tool

downloadRadiko(){
    echo "Downloading radiko original apk"
    DOWNLOADLINK=`curl -s  https://apkpure.com/radiko-jp-for-android/jp.radiko.Player/download/77-APK  |grep -oP "(?<=id=\"iframe_download\" src=\").*?(?=\")"`
    if [-z $DOWNLOADLINK];then
        wget -O $BUILDTOOLDIR/src.apk -nc $DOWNLOADLINK || exit 1
    else
        exit 1
    fi
}

downloadApktool(){
    echo "Downloading Apktool"
    wget -P $BUILDTOOLDIRi -nc https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.3.2.jar || exit 1
}


echo "Using " $BUILDTOOLDIR " for apktool and radiko original android apk"
if [! -x "$BUILDTOOLDIR"];then
    mkdir $BUILDTOOLDIR
    downloadRadiko
    downloadApktool
else
    if [! -a $BUILDTOOLDIR/src.apk] || [ `md5sum $BUILDTOOLDIR/src.apk |awk '{print $1}'` -eq '5331083aef76176cc668b181b87b750d' ] ;then
        downloadRadiko
    fi
    if [! -a $BUILDTOOLDIR/apktool_2.3.2.jar ] || [ `md5sum $BUILDTOOLDIR/apktool_2.3.2.jar |awk '{print $1}'` -eq '953ed8a553becac4e713d1073912f15f'];then
        downloadApktool
    fi
fi

BUILDDIR=`mktemp -d`
echo "Create tmp build directory" $BUILDDIR
echo "Decompiling"
java -jar $BUILDTOOLDIR/apktool_2.3.2.jar d $BUILDTOOLDIR/src.apk -f -o $BUILDDIR
echo "Applying patch from " $MYDIR/v6.3.6.patch
cd $BUILDDIR 
git apply --stat $MYDIR/v6.3.6.patch
git apply $MYDIR/v6.3.6.patch
echo "Compiling && Packaging && Signing"
java -jar $BUILDTOOLDIR/apktool_2.3.2.jar b $BUILDDIR
cd $BUILDDIR/dist && keytool -genkey -keystore fake.keystore -alias fake  -storepass 123456 -dname "CN=fake" -keypass 123456  -validity 36500 && jarsigner -keystore fake.keystore -storepass 123456 -signedjar $MYDIR/radiko_kai_6.3.6.apk src.apk fake 
echo "Removing tmp directory" $BUILDDIR
rm -r $BUILDDIR
echo "Result is " $MYDIR/radiko_kai_6.3.6.apk
cd $CURDIR
