#!/usr/bin/env python2
'''
Requirements:
1) Python dependencies: pyelftools capstone
2) Git,Java,diff

'''
import re
import subprocess
import sys
import tempfile
import urllib

from os.path import exists as pathexists
from os.path import join as pathjoin
from shutil import copytree

from .parser import parse as soparse

APK_URL = "https://apkpure.com/radiko-jp-for-android/jp.radiko.Player"


APKINFO_PATTERN = r"Version: </strong>(?P<ver>[\d|\.]*) "

APK_DOWNINFO = "https://apkpure.com/radiko-jp-for-android/"
"jp.radiko.Player/download/{0}-APK"

APKTOOL_LINK = "https://bitbucket.org/iBotPeaches/"
"apktool/downloads/apktool_2.3.2.jar"

r"\((?P<numver>\d*?)\).*?Update on: </strong>"
r"(?P<update>[\d|-]*).*?SHA1: </strong>(?P<sha1>\w{40})"


def get_versions():
    page = urllib.urlopen(APK_URL).read()
    res = [re.search(APKINFO_PATTERN, item, re.M | re.S).groupdict()
           for item in re.findall(r'''<dd style.*?</dd>''', page, re.M | re.S)]
    res.sort(key=lambda x: int(x['numver']), reverse=True)
    return res


def download_apk(info, dstpath):
    page = urllib.urlopen(APK_DOWNINFO.format(info['numver'])).read()
    link = re.findall(r'(?<=id=\"iframe_download\" src=\").*?(?=\")', page)[0]
    dstfile = pathjoin(dstpath, "{0}.apk".format(info["ver"]))
    return urllib.urlretrieve(link, dstfile)


def download_apktool(dstpath):
    dstfile = pathjoin(dstpath, "apktool_2.3.2.jar")
    return urllib.urlretrieve(APKTOOL_LINK, dstfile)


def get_noticing_smali(smali_patch_file):
    with open(smali_patch_file, 'r') as f:
        content = f.read()
        return re.findall(r"a/(.*?\.smali$)", content)


def check_stable(noticing_smali, lastest_d_path, cmpver_d_path):
    for smali in noticing_smali:
        dst = pathjoin(lastest_d_path, smali)
        src = pathjoin(cmpver_d_path, smali)
        if not pathexists(dst) or not pathexists(src):
            return False
        with open(dst, "r") as f1:
            content1 = f1.read()
            with open(src, "r") as f2:
                content2 = f2.read()
                if content2 != content1:
                    return False
    return True


def main():
    versions = get_versions()
    latest = versions[0]
    if pathexists(pathjoin("./patch", latest['ver'])):
        print("No updates!")
        return 0
    else:
        workdir = tempfile.mkdtemp()
        print("Work Directory:{0}".format(workdir))
        latest_file, _ = download_apk(latest, workdir)
        lastest_d_path = pathjoin(workdir, latest["ver"])
        for item in range(1, len(versions)):
            if pathexists(pathjoin("./patch", item['ver'])):
                break
        else:
            print("Nothing Comparable!")
            # clean up
            # 1. delete latest_file 2. delete workdir
            return 1
        cmpver = item
        cmpver_file, _ = download_apk(cmpver, workdir)
        cmpver_d_path = pathjoin(workdir, cmpver["ver"])
        apktool_file, _ = download_apktool(workdir)
        ret = subprocess.call(["java", "-jar", apktool_file, "d", "-f", "-o",
                               lastest_d_path, latest_file])
        if ret != 0:
            print("Decompiled Error!")
            # cleanup
            return 1
        ret = subprocess.call(["java", "-jar", apktool_file, "d", "-f", "-o",
                               cmpver_d_path, cmpver_file])
        if ret != 0:
            print("Decompiled Error!")
            # cleanup
            return 1

        cmp_smali_patch = pathjoin("./patch", cmpver["ver"], "smali.patch")
        noticing_smali = get_noticing_smali(cmp_smali_patch)
        if not check_stable(noticing_smali, lastest_d_path, cmpver_d_path):
            # cleanup
            return 1
        latest_lib_path = pathjoin(lastest_d_path, "lib")
        latest_lib_kai_path = pathjoin(lastest_d_path, "lib_kai")
        copytree(latest_lib_path, latest_lib_kai_path)
        # for loop
        # make patch/latest dir and copy cmp_smali_patch & generate so patch

    pass


if __name__ == '__main__':
    sys.exit(main())
