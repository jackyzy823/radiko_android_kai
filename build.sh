MYDIR=`pwd`
BUILDDIR=$MYDIR/build
# BUILDDIR=`/tmp/radiko_build` #could be anywhere except git project dir.
rm -rf .git  #if builddir in git project folder then delete .git folder
wget -O src.apk `curl -s  https://apkpure.com/radiko-jp-for-android/jp.radiko.Player/download/77-APK  |grep -oP "(?<=id=\"iframe_download\" src=\").*?(?=\")"`
wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.3.2.jar
java -jar apktool_2.3.2.jar d src.apk -f -o $BUILDDIR
cd $BUILDDIR && git apply $MYDIR/v6.3.6.patch
cd $MYDIR && java -jar apktool_2.3.2.jar b $BUILDDIR
cd $BUILDDIR/dist && keytool -genkey -keystore fake.keystore -alias fake  -storepass 123456 -dname "CN=fake" -keypass 123456  -validity 36500 && jarsigner -keystore fake.keystore -storepass 123456 -signedjar $MYDIR/radiko_kai_6.3.6.apk src.apk fake && rm -r $BUILDDIR
