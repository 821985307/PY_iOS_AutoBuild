#!/usr/bin/env python
# -*- coding:utf-8 -*-



import argparse
import subprocess
import requests
import os
import datetime
import json
from biplist import *
import zipfile, biplist, sys, re



# 打包配置
CONFIGURATION = "Release"
EXPORT_OPTIONS_PLIST = "/Users/wzz/Desktop/Git/ios_movie_searcher_dev_wzz/exportOptions.plist"
WORKSPACE = "/Users/wzz/Desktop/Git/ios_movie_searcher_dev_wzz/video.xcworkspace"
PLIST_PATH = "/Users/wzz/Desktop/Git/ios_movie_searcher_dev_wzz/video/Others/Info.plist"
TARGET = 'video'
SCHEME = 'video_pre'



# 输出路径
DATE = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
EXPORT_MAIN_DIRECTORY = "~/Desktop/ipa/" + SCHEME + DATE
ARCHIVEPATH = EXPORT_MAIN_DIRECTORY + "/%s.xcarchive" %(SCHEME)
IPAPATH = EXPORT_MAIN_DIRECTORY + "/%s.ipa" %(SCHEME)



# 蒲公英相关参数
PGYER_UPLOAD_URL = "http://www.pgyer.com/apiv1/app/upload"
DOWNLOAD_BASE_URL = "http://www.pgyer.com"
USER_KEY = "f1f35f24d79fa67a131ec31531bad658"
API_KEY = "68c801c712051ecfe705e5c843b1b738"
REMARK = ""




# 上传到AppConnect
#def uploadIpaToAppStore():
#
#	print "iPA上传中...."
#	altoolPath = "/Applications/Xcode.app/Contents/Applications/Application\ Loader.app/Contents/Frameworks/ITunesSoftwareService.framework/Versions/A/Support/altool"
#
#	exportCmd = "%s --validate-app -f %s -u %s -p %s -t ios --output-format xml" % (altoolPath, IPAPATH, APPLEID,APPLEPWD)
#	process = subprocess.Popen(exportCmd, shell=True)
#	(stdoutdata, stderrdata) = process.communicate()
#
#	validateResult = process.returncode
#	if validateResult == 0:
#		print '~~~~~~~~~~~~~~~~iPA验证通过~~~~~~~~~~~~~~~~'
#		exportCmd = "%s --upload-app -f %s -u %s -p %s -t ios --output-format normal" % (
#		altoolPath, IPAPATH, APPLEID, APPLEPWD)
#		process = subprocess.Popen(exportCmd, shell=True)
#		(stdoutdata, stderrdata) = process.communicate()
#
#		uploadresult = process.returncode
#		if uploadresult == 0:
#			print '~~~~~~~~~~~~~~~~iPA上传成功'
#		else:
#			print '~~~~~~~~~~~~~~~~iPA上传失败'
#	else:
#		print "~~~~~~~~~~~~~~~~iPA验证失败~~~~~~~~~~~~~~~~"

def parserUploadResult(jsonResult):
    print "上传蒲公英成功"
    
    ipaPath = os.path.expanduser(IPAPATH)
    ipaPath = unicode(ipaPath, "utf-8")
    version = analyze_ipa_with_plistlib(ipaPath)

    downUrl = DOWNLOAD_BASE_URL +"/"+jsonResult['data']['appShortcutUrl']

    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "link",
        "link": {
            "title": SCHEME + " 已更新至 " + version + "csxc",
            "text": REMARK,
            "messageUrl": downUrl
        }
    }
    s = json.dumps(payload)
    r = requests.post("https://oapi.dingtalk.com/robot/send?access_token=fde00de18ee2b0a84dc27b99da26bf099aa2091f9e9687106f65d33d6475d282", data = s,headers = headers)
        
    
    if r.status_code == requests.codes.ok:
        print "通知成功"


# 上传蒲公英
def uploadIpaToPgyer():
	ipaPath = os.path.expanduser(IPAPATH)
	ipaPath = unicode(ipaPath, "utf-8")
	files = {'file': open(ipaPath, 'rb')}
	headers = {'enctype':'multipart/form-data'}
	payload = {'uKey':USER_KEY,'_api_key':API_KEY,'updateDescription':REMARK}
	print "uploading...."
	r = requests.post(PGYER_UPLOAD_URL, data = payload ,files=files,headers=headers)
	if r.status_code == requests.codes.ok:
		result = r.json()
		parserUploadResult(result)
	else:
		print 'HTTPError,Code:'+r.status_code





# 分析IPA文件
def analyze_ipa_with_plistlib(ipa_path):
     ipa_file = zipfile.ZipFile(ipa_path)
     plist_path = find_plist_path(ipa_file)
     plist_data = ipa_file.read(plist_path)
     plist_root = biplist.readPlistFromString(plist_data)
     return plist_root['CFBundleShortVersionString'] + "_" + plist_root['CFBundleVersion']
 


def find_plist_path(zip_file):
     name_list = zip_file.namelist()
     # print name_list
     pattern = re.compile(r'Payload/[^/]*.app/Info.plist')
     for path in name_list:
         m = pattern.match(path)
         if m is not None:
             return m.group()


# 自动化打包
def autoPackage():
        # 打包
        archiveReturnCode = xcbuild()
        # 如果打包成功 导出ipa
        if archiveReturnCode == 0:
            signReturnCode = exportArchive()
            
            # 上传ipa到蒲公英
            if signReturnCode == 0:
                uploadIpaToPgyer()
                


# 调用xcode命令打包
def xcbuild():
        # 判断是 xcodeproj 还是  xcworkspace
        projectArg = "project"
        if WORKSPACE.find("xcworkspace")>=0:
            projectArg = "workspace"
            
        # 调用xcode命令进行ARCHIVE
        archiveCmd = 'xcodebuild -%s %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS' %(projectArg, WORKSPACE, SCHEME, CONFIGURATION, ARCHIVEPATH)
        process = subprocess.Popen(archiveCmd, shell=True)
        process.wait()
        
        # 判断打包结果 如果打包失败 删除ARCHIVE相关的内容
        archiveReturnCode = process.returncode
        if archiveReturnCode != 0:
            print "archive project %s failed" %(project)
            cleanCmd = "rm -r %s" %(ARCHIVEPATH)
            process = subprocess.Popen(cleanCmd, shell = True)
            process.wait()
            print "cleaned archiveFile: %s" %(ARCHIVEPATH)
        # 打包成功 使用ARCHIVE 导出IPA
        else:
            return archiveReturnCode




# archive结果导出ipa
def exportArchive():
    exportCmd = "xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s" %(ARCHIVEPATH, EXPORT_MAIN_DIRECTORY, EXPORT_OPTIONS_PLIST)
    process = subprocess.Popen(exportCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()
    signReturnCode = process.returncode
    return signReturnCode



# 主函数
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-r",help="更新备注")
    options = parser.parse_args()

    if options.r:
        REMARK = options.r
        autoPackage()
    else:
        print "请输入更新备注"

    
if __name__ == '__main__':
    main()
