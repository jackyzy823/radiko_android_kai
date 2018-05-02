CURDIR=`pwd`
MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script is in the" $MYDIR
BUILDTOOLDIR=$MYDIR/build-tool
echo "Using " $BUILDTOOLDIR " for apktool and radiko original android apk"
echo "Downloading radiko original apk"
# BUILDDIR=`/tmp/radiko_build` #could be anywhere except git project dir.
#rm -rf .git  #if builddir in git project folder then delete .git folder
DOWNLOADLINK=curl -s  https://apkpure.com/radiko-jp-for-android/jp.radiko.Player/download/77-APK  |grep -oP "(?<=id=\"iframe_download\" src=\")    .*?(?=\")"
wget -O $BUILDTOOLDIR/src.apk -nc $DOWNLOADLINK
wget -P $BUILDTOOLDIR https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.3.2.jar
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
