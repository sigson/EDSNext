#!/usr/bin/python3

import os
import sys
import subprocess
from enum import Enum
import re
import shutil

ARG_STORAGE_TYPE = "storage"
ARG_READ_ONLY = "ro"

STORAGE_TYPE_FS = "fs"
STORAGE_TYPE_ROOT = "root"
STORAGE_TYPE_SAF = "saf"
STORAGE_TYPE_SAFRO = "safro"
STORAGE_TYPE_VIRTUAL = "virtual"

VALID_STORAGE_TYPES = [STORAGE_TYPE_FS, STORAGE_TYPE_ROOT, STORAGE_TYPE_SAF, STORAGE_TYPE_SAFRO, STORAGE_TYPE_VIRTUAL]

HOSTNAME = "localhost"
PORT_SFTP = "1234"
PORT_FTP = "12345"
PORT_FTP_PASSIVE = "5678"

CMD_ADB_PORT_SFTP = "adb forward tcp:" + PORT_SFTP + " tcp:" + PORT_SFTP
CMD_ADB_PORT_FTP = "adb forward tcp:" + PORT_FTP + " tcp:" + PORT_FTP
CMD_ADB_PORT_FTP_PASSIVE = "adb forward tcp:" + PORT_FTP_PASSIVE + " tcp:" + PORT_FTP_PASSIVE

BASE_URL_SFTP =   "sftp://" + HOSTNAME + ":" + PORT_SFTP
BASE_URL_FTP =    "ftp://" + HOSTNAME + ":" + PORT_FTP

DEFAULT_PATH_FS = "/storage/emulated/0/"
DEFAULT_PATH_ROOT = "/storage/emulated/0/"
DEFAULT_PATH_SAF = "/"
DEFAULT_PATH_ROSAF = "/"

DEFAULT_PATH_VIRTUAL_FS = "/fs" + DEFAULT_PATH_FS
DEFAULT_PATH_VIRTUAL_ROOT = "/superuser" + DEFAULT_PATH_ROOT
DEFAULT_PATH_VIRTUAL_SAF = "/saf" + DEFAULT_PATH_SAF
DEFAULT_PATH_VIRTUAL_ROSAF = "/rosaf" + DEFAULT_PATH_ROSAF

KEY_FILE_RSA = "rsa.key"
KEY_FILE_DSA = "dsa.key"
KEY_FILE_ECDSA = "ecdsa.key"
KEY_FILE_ECDSA_384 = "ecdsa.key.384"
KEY_FILE_ECDSA_521 = "ecdsa.key.521"
KEY_FILE_ED25519 = "ed25519.key"
KEY_FILE_RSA_BAD = "rsa.bad.key"
KEY_FILE_ED25519_BAD = "ed25519.bad.key"

CURRENT_DIR = os.path.dirname(__file__)
KEY_DIR = os.path.join(CURRENT_DIR, "../pftpd-pojo-lib/src/test/resources/keys")
KEY_PATH = KEY_DIR + "/" + KEY_FILE_ED25519
KEY_PATH_RSA = KEY_DIR + "/" + KEY_FILE_RSA
KEY_PATH_DSA = KEY_DIR + "/" + KEY_FILE_DSA
KEY_PATH_ECDSA = KEY_DIR + "/" + KEY_FILE_ECDSA
KEY_PATH_ECDSA_384 = KEY_DIR + "/" + KEY_FILE_ECDSA_384
KEY_PATH_ECDSA_521 = KEY_DIR + "/" + KEY_FILE_ECDSA_521
KEY_PATH_RSA_BAD = KEY_DIR + "/" + KEY_FILE_RSA_BAD
KEY_PATH_ED25519_BAD = KEY_DIR + "/" + KEY_FILE_ED25519_BAD

DEFAULT_TIMEOUT = " --max-time 5"
OPTS_SFTP_BASE = "-vk" + DEFAULT_TIMEOUT
OPTS_SFTP_NO_KEY = OPTS_SFTP_BASE + " --key "
DEFAULT_OPTS_SFTP = OPTS_SFTP_NO_KEY + KEY_PATH
OPTS_USER_PASS = "--user user:test"
DEFAULT_OPTS_FTP = "-v " + OPTS_USER_PASS + DEFAULT_TIMEOUT
DEFAULT_OPTS_SCP = "-i " + KEY_PATH + " -P " + PORT_SFTP + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PreferredAuthentications=publickey"

NEW_DIR = "test-dir-auto"
NEW_DIR_RENAMED = "test-dir-auto-renamed"
SUB_DIR = "sub-dir"
SUB_DIR_RENAMED = "sub-dir-renamed"
PRE_EXISTING_TEST_DIR = "test-dir"

TEST_FILE_NAME = "testfile"
TEST_FILE_PATH = os.path.join(CURRENT_DIR, TEST_FILE_NAME)
TEST_FILE_SIZE = os.path.getsize(TEST_FILE_PATH)
TEST_FILE_NAME_RENAMED = "testfile-renamed"

TMP_DIR = "/tmp/pftpd-tests"

class Protocol(Enum):
    FTP = 1
    SFTP = 2

def runCommand(cmd, check = True):
    print("running command: " + cmd)
    pieces = cmd.split()

    # check if pieces contain qote -> must be handled as one piece
    unifiedPieces = []
    quoteOpen = False
    for i in range(len(pieces)):
        piece = pieces[i]
        if piece[:1] == "\"":
            quoteOpen = True
            for j in range(i + 1, len(pieces)):
                piece2 = pieces[j]
                if "\"" in piece2:
                    unifiedPiece = ""
                    separator = ""
                    for k in range(i, j + 1):
                        unifiedPiece = unifiedPiece + separator + pieces[k]
                        separator = " "
                    # and strip quotes
                    unifiedPiece = unifiedPiece[1 : len(unifiedPiece) - 1]
                    unifiedPieces.append(unifiedPiece)
                    break
                j = j + 1
        elif piece[-1] == "\"":
            quoteOpen = False
        else:
            if not quoteOpen:
                unifiedPieces.append(piece)
        i = i + 1

    proc = subprocess.run(unifiedPieces, stdout=subprocess.PIPE, check=check)
    return str(proc.stdout.decode("utf-8"))

def setupAdbForwards():
    runCommand(CMD_ADB_PORT_SFTP)
    runCommand(CMD_ADB_PORT_FTP)
    runCommand(CMD_ADB_PORT_FTP_PASSIVE)

def setupTmpDir():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.mkdir(TMP_DIR)

def log(msg):
    print("\n")
    print("**************************** " + msg)
    print("\n")

def check(value, text, errors, msg):
    if not type(text) is str or not value in text:
        errors.append(msg + value)

def checkExp(exp, text, errors, msg):
    found = False
    if type(text) is str:
        matchobject = re.match(exp, text)
        if not matchobject is None:
            found = True
    if not found == True:
        errors.append(msg + exp)

def checkNot(value, text, errors, msg):
    if not type(text) is str or value in text:
        errors.append(msg + value)

def checkEmpty(errors, text, msgPrefix):
    log("checking if empty\n" + text)
    if len(text) > 0:
        errors.append(msgPrefix + " not empty")

def checkHomeListing(errors, text, msgPrefix, storageType, newDirPresent = False, dirRenamed = False):
    log("checking home listing\n" + text)
    msg = msgPrefix + " missing dir in home: "
    msgPresent = msgPrefix + " present dir in home: "
    check("Android", text, errors, msg)
    check("DCIM", text, errors, msg)
    check("test-dir", text, errors, msg)
    if newDirPresent:
        dirName = NEW_DIR if not dirRenamed else NEW_DIR_RENAMED
        check(dirName, text, errors, msg)
    else:
        checkNot(NEW_DIR, text, errors, msgPresent)
        checkNot(NEW_DIR_RENAMED, text, errors, msgPresent)
    if not (storageType == STORAGE_TYPE_SAF or storageType == STORAGE_TYPE_SAFRO or storageType == STORAGE_TYPE_VIRTUAL):
        checkNot(SUB_DIR, text, errors, msgPresent)

def checkListingLevel1(errors, text, msgPrefix, subDirPresent = True, subDirRenamed = False):
    log("checking listing (level 1)\n" + text)
    msg = msgPrefix + " missing dir: "
    msgPresent = msgPrefix + " present dir: "
    if subDirPresent:
        subdirName = SUB_DIR if not subDirRenamed else SUB_DIR_RENAMED
        check(subdirName, text, errors, msg)
    else:
        checkNot(SUB_DIR, text, errors, msgPresent)
        checkNot(SUB_DIR_RENAMED, text, errors, msgPresent)

def checkListingLevel2(errors, text, msgPrefix, filePresent = True, afterRename = False):
    log("checking listing (level 2)\n" + text)
    msg = msgPrefix + " missing file: "
    msgFileSize = msgPrefix + " wrong upload filezise: "
    msgPresent = msgPrefix + " present file: "
    if filePresent:
        filename = TEST_FILE_NAME if not afterRename else TEST_FILE_NAME_RENAMED
        check(filename, text, errors, msg)
        filesizeTest = "(.*) " + str(TEST_FILE_SIZE) + " (... .. ..:..) " + filename + ""
        checkExp(filesizeTest, text, errors, msgFileSize)
    else:
        checkNot(TEST_FILE_NAME, text, errors, msgPresent)
        checkNot(TEST_FILE_NAME_RENAMED, text, errors, msgPresent)

def checkDownloadedFile(errors, filename, errorTag):
    log("checking downloaded file: " + filename)
    tmpPath = TMP_DIR + "/" + filename

    output = runCommand("ls -lh " + TMP_DIR)
    print(output)

    if os.path.exists(tmpPath):
        output = runCommand("cat " + tmpPath)
        print(output)

        size = os.path.getsize(tmpPath)
        if TEST_FILE_SIZE != size:
            errors.append(errorTag + " bad local filesize: " + filename + ", size: " + str(size))
    else:
        errors.append(errorTag + " missing local file: " + filename)

def downloadListing(url, protocol, key = KEY_PATH, check = True):
    log("downloading url: " + url)
    opts = (OPTS_SFTP_NO_KEY + key) if (protocol == Protocol.SFTP) else DEFAULT_OPTS_FTP
    cmd = "curl " + opts + " " + url
    return runCommand(cmd, check)

def downloadListingSftpPassword(url, check = True):
    log("downloading url (with username & password): " + url)
    opts = OPTS_SFTP_BASE + " " + OPTS_USER_PASS
    cmd = "curl " + opts + " " + url
    return runCommand(cmd, check)

def upload(url, protocol):
    log("uploading to: " + url)
    opts = DEFAULT_OPTS_SFTP if (protocol == Protocol.SFTP) else DEFAULT_OPTS_FTP
    cmd = "curl " + opts + " -T " + TEST_FILE_PATH + " " + url
    return runCommand(cmd)

def download(url, filename, protocol):
    log("downloading: " + url + filename)
    opts = DEFAULT_OPTS_SFTP if (protocol == Protocol.SFTP) else DEFAULT_OPTS_FTP
    cmd = "curl " + opts + " -o " + TMP_DIR + "/" + filename + " " + url + filename
    return runCommand(cmd)

def sendCommand(baseUrl, remoteCmd, protocol):
    opts = DEFAULT_OPTS_SFTP if (protocol == Protocol.SFTP) else DEFAULT_OPTS_FTP
    cmd = "curl " + opts + " " + baseUrl + " " + remoteCmd
    return runCommand(cmd)

def createDir(baseUrl, remoteBasePath, newDir, protocol):
    log("creating dir: " + baseUrl + remoteBasePath + " " + newDir)
    remoteCmd = ""
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"MKDIR " + newDir + "\""
    else:
        remoteCmd = "-Q \"MKD " + newDir + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def createSubDir(baseUrl, remoteBasePath, dirs, protocol):
    log("creating sub dir: " + baseUrl + remoteBasePath + " " + str(dirs))
    remoteCmd = ""
    path = buildSubPath(dirs)
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"MKDIR " + path + "\""
    else:
        remoteCmd = "-Q \"MKD " + path + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def removeDir(baseUrl, remoteBasePath, dir, protocol):
    log("removing dir: " + baseUrl + remoteBasePath + " " + dir)
    remoteCmd = ""
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"RMDIR " + dir + "\""
    else:
        remoteCmd = "-Q \"RMD " + dir + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def removeSubDir(baseUrl, remoteBasePath, dirs, protocol):
    log("removing sub dir: " + baseUrl + remoteBasePath + " " + str(dirs))
    remoteCmd = ""
    path = buildSubPath(dirs)
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"RMDIR " + path + "\""
    else:
        remoteCmd = "-Q \"RMD " + path + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def removeFile(baseUrl, remoteBasePath, dirs, filename, protocol):
    log("removing file: " + baseUrl + remoteBasePath + " " + str(dirs) + " " + filename)
    remoteCmd = ""
    path = buildSubPath(dirs)
    path += "/" + filename
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"RM " + path + "\""
    else:
        remoteCmd = "-Q \"DELE " + path + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def rename(baseUrl, remoteBasePath, dirs, oldName, newName, protocol):
    log("renaming file: " + baseUrl + remoteBasePath + " " + str(dirs) + " " + oldName + " to " + newName)
    remoteCmd = ""
    path = buildSubPath(dirs)
    print("  path: " + path + ", len: " + str(len(path)))
    if len(path) > 0:
        path += "/"
    oldPath = path + oldName
    newPath = path + newName
    if protocol == Protocol.SFTP:
        remoteCmd = "-Q \"RENAME " + oldPath + " " + newPath + "\""
    else:
        remoteCmd = "-Q \"RNFR " + oldPath + "\""
        remoteCmd += " -Q \"RNTO " + newPath + "\""
    return sendCommand(baseUrl + remoteBasePath, remoteCmd, protocol)

def buildSubPath(dirs):
    path = ""
    separator = ""
    for dir in dirs:
        path += separator + dir
        separator = "/"
    return path


def uploadScp(path):
    log("scp upload " + path)
    cmd = "scp " + DEFAULT_OPTS_SCP + " " + TEST_FILE_PATH + " " + HOSTNAME + ":" + path
    return runCommand(cmd)

def downloadScp(remotePath, tmpPath):
    log("scp download " + remotePath)
    cmd = "scp " + DEFAULT_OPTS_SCP + " " + HOSTNAME + ":" + remotePath + " " + tmpPath
    return runCommand(cmd)


def testCycle(baseUrl, remoteBasePath, errorTag, errors, protocol, storageType):
    setupTmpDir()

    # check listing of home dir
    output = downloadListing(baseUrl + remoteBasePath, protocol)
    checkHomeListing(errors, output, errorTag, storageType)
    # if we have errors that early it is not worth continuing
    if len(errors) > 0:
        print("abort due to errors\n")
        return

    # create dir
    output = createDir(baseUrl, remoteBasePath, NEW_DIR, protocol)
    checkHomeListing(errors, output, errorTag, storageType, newDirPresent = True)

    # create sub-dir
    createSubDir(baseUrl, remoteBasePath, [NEW_DIR, SUB_DIR], protocol)
    output = downloadListing(baseUrl + remoteBasePath + NEW_DIR + "/", protocol)
    checkListingLevel1(errors, output, errorTag)

    # upload file
    url = baseUrl + remoteBasePath + NEW_DIR + "/" + SUB_DIR + "/"
    upload(url, protocol)
    output = downloadListing(url, protocol)
    checkListingLevel2(errors, output, errorTag)

    # download file
    download(url, TEST_FILE_NAME, protocol)
    checkDownloadedFile(errors, TEST_FILE_NAME, errorTag)

    # rename file
    rename(baseUrl, remoteBasePath, [NEW_DIR, SUB_DIR], TEST_FILE_NAME, TEST_FILE_NAME_RENAMED, protocol)
    output = downloadListing(url, protocol)
    checkListingLevel2(errors, output, errorTag, filePresent = True, afterRename = True)

    # download again
    download(url, TEST_FILE_NAME_RENAMED, protocol)
    checkDownloadedFile(errors, TEST_FILE_NAME_RENAMED, errorTag)

    # rename sub-dir
    rename(baseUrl, remoteBasePath, [NEW_DIR], SUB_DIR, SUB_DIR_RENAMED, protocol)
    output = downloadListing(baseUrl + remoteBasePath + NEW_DIR + "/", protocol)
    checkListingLevel1(errors, output, errorTag, subDirPresent = True, subDirRenamed = True)

    # rename dir
    rename(baseUrl, remoteBasePath, [], NEW_DIR, NEW_DIR_RENAMED, protocol)
    output = downloadListing(baseUrl + remoteBasePath, protocol)
    checkHomeListing(errors, output, errorTag, storageType, newDirPresent = True, dirRenamed = True)
    url = baseUrl + remoteBasePath + NEW_DIR_RENAMED + "/" + SUB_DIR_RENAMED + "/"

    # delete file
    removeFile(baseUrl, remoteBasePath, [NEW_DIR_RENAMED, SUB_DIR_RENAMED], TEST_FILE_NAME_RENAMED, protocol)
    output = downloadListing(url, protocol)
    checkListingLevel2(errors, output, errorTag, filePresent = False)

    # delete sub-dir
    removeSubDir(baseUrl, remoteBasePath, [NEW_DIR_RENAMED, SUB_DIR_RENAMED], protocol)
    output = downloadListing(baseUrl + remoteBasePath + NEW_DIR_RENAMED + "/", protocol)
    checkListingLevel1(errors, output, errorTag, subDirPresent = False)

    # delete dir
    output = removeDir(baseUrl, remoteBasePath, NEW_DIR_RENAMED, protocol)
    checkHomeListing(errors, output, errorTag, storageType)


def testCycleReadOnly(baseUrl, remoteBasePath, errorTag, errors, protocol, storageType):
    setupTmpDir()

    # check listing of home dir
    output = downloadListing(baseUrl + remoteBasePath, protocol)
    checkHomeListing(errors, output, errorTag, storageType)
    # if we have errors that early it is not worth continuing
    if len(errors) > 0:
        return

    # check listing of first dir
    url = baseUrl + remoteBasePath + PRE_EXISTING_TEST_DIR + "/"
    output = downloadListing(url, protocol)
    checkListingLevel1(errors, output, errorTag)

    # check listing of first dir
    url += SUB_DIR + "/"
    output = downloadListing(baseUrl + remoteBasePath + PRE_EXISTING_TEST_DIR + "/", protocol)
    checkListingLevel2(errors, output, errorTag)

    # download file
    download(url, TEST_FILE_NAME, protocol)
    checkDownloadedFile(errors, TEST_FILE_NAME, errorTag)


def scpUpload(baseUrl, remoteBasePath, errorTag, errors):
    protocol = Protocol.SFTP
    createDir(baseUrl, remoteBasePath, NEW_DIR, protocol)
    createSubDir(baseUrl, remoteBasePath, [NEW_DIR, SUB_DIR], protocol)

    uploadScp(NEW_DIR + "/" + SUB_DIR)
    url = baseUrl + remoteBasePath + NEW_DIR + "/" + SUB_DIR + "/"
    output = downloadListing(url, protocol)
    checkListingLevel2(errors, output, errorTag)

    removeFile(baseUrl, remoteBasePath, [NEW_DIR, SUB_DIR], TEST_FILE_NAME, protocol)
    removeSubDir(baseUrl, remoteBasePath, [NEW_DIR, SUB_DIR], protocol)
    removeDir(baseUrl, remoteBasePath, NEW_DIR, protocol)


def scpDownload(remoteBasePath, errorTag, errors):
    setupTmpDir()
    tmpPath = TMP_DIR + "/" + TEST_FILE_NAME
    remotePath = remoteBasePath + PRE_EXISTING_TEST_DIR + "/" + SUB_DIR + "/" + TEST_FILE_NAME
    downloadScp(remotePath, tmpPath)
    checkDownloadedFile(errors, TEST_FILE_NAME, errorTag)


def testKeys(baseUrl, errors):
    protocol = Protocol.SFTP
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_DSA)
    checkHomeListing(errors, output, "[key dsa]", storageType)
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_RSA)
    checkHomeListing(errors, output, "[key rsa]", storageType)
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_ECDSA)
    checkHomeListing(errors, output, "[key ecdsa]", storageType)
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_ECDSA_384)
    checkHomeListing(errors, output, "[key ecdsa 384]", storageType)
    # check bad keys
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_RSA_BAD, check = False)
    checkEmpty(errors, output, "[key bad rsa]")
    output = downloadListing(baseUrl, protocol, key = KEY_PATH_ED25519_BAD, check = False)
    checkEmpty(errors, output, "[key bad ed25519]")
    # check username & password for sftp
    output = downloadListingSftpPassword(baseUrl)
    checkHomeListing(errors, output, "[sftp password]", storageType)


############################################################################
# main

# parse commandline
storageType = ""
readOnly = False
for i in range(len(sys.argv)):
    arg = sys.argv[i]
    if arg == ARG_STORAGE_TYPE or arg == "--" + ARG_STORAGE_TYPE:
        if i < len(sys.argv) - 1:
            storageType = sys.argv[i + 1]
            i = i+1
    elif arg == ARG_READ_ONLY or arg == "--" + ARG_READ_ONLY:
        readOnly = True

if not storageType in VALID_STORAGE_TYPES:
    print("no valid storage type (got: " + storageType + ")")
    sys.exit(-1)

# start tests
setupAdbForwards()

errors = []
if storageType == STORAGE_TYPE_FS:
    if readOnly:
        testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_FS, "[fs sftp]", errors, Protocol.SFTP, storageType)
        testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_FS,  "[fs  ftp]", errors, Protocol.FTP, storageType)
    else:
        testCycle(BASE_URL_SFTP, DEFAULT_PATH_FS, "[fs sftp]", errors, Protocol.SFTP, storageType)
        testCycle(BASE_URL_FTP, DEFAULT_PATH_FS,  "[fs  ftp]", errors, Protocol.FTP, storageType)
        scpUpload(BASE_URL_SFTP, DEFAULT_PATH_FS, "[fs  scp]", errors)
    scpDownload(DEFAULT_PATH_FS, "[fs  scp]", errors)
    testKeys(BASE_URL_SFTP + DEFAULT_PATH_FS, errors)

if storageType == STORAGE_TYPE_ROOT:
    if readOnly:
        testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_ROOT, "[root sftp]", errors, Protocol.SFTP, storageType)
        testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_ROOT,  "[root  ftp]", errors, Protocol.FTP, storageType)
    else:
        testCycle(BASE_URL_SFTP, DEFAULT_PATH_ROOT, "[root sftp]", errors, Protocol.SFTP, storageType)
        testCycle(BASE_URL_FTP, DEFAULT_PATH_ROOT,  "[root  ftp]", errors, Protocol.FTP, storageType)
        # note: scp upload with root causes known error: filesize is 0
        scpUpload(BASE_URL_SFTP, DEFAULT_PATH_ROOT, "[root  scp]", errors)
    # scp download with root causes EOFException in ScpHelper.readAck, even with copy-to-tmp
    #scpDownload(DEFAULT_PATH_ROOT, "[root  scp]", errors)
    testKeys(BASE_URL_SFTP + DEFAULT_PATH_ROOT, errors)

if storageType == STORAGE_TYPE_SAF:
    if readOnly:
        testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_SAF, "[SAF sftp]", errors, Protocol.SFTP, storageType)
        testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_SAF,  "[SAF  ftp]", errors, Protocol.FTP, storageType)
    else:
        testCycle(BASE_URL_SFTP, DEFAULT_PATH_SAF, "[SAF sftp]", errors, Protocol.SFTP, storageType)
        testCycle(BASE_URL_FTP, DEFAULT_PATH_SAF,  "[SAF  ftp]", errors, Protocol.FTP, storageType)
        scpUpload(BASE_URL_SFTP, DEFAULT_PATH_SAF, "[SAF  scp]", errors)
    scpDownload(DEFAULT_PATH_SAF, "[SAF  scp]", errors)
    testKeys(BASE_URL_SFTP + DEFAULT_PATH_SAF, errors)

if storageType == STORAGE_TYPE_SAFRO:
    testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_ROSAF, "[SAFRO sftp]", errors, Protocol.SFTP, storageType)
    testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_ROSAF,  "[SAFRO  ftp]", errors, Protocol.FTP, storageType)
    scpDownload(DEFAULT_PATH_ROSAF, "[SAFRO  scp]", errors)
    testKeys(BASE_URL_SFTP + DEFAULT_PATH_ROSAF, errors)

if storageType == STORAGE_TYPE_VIRTUAL:
    try:
        testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_FS, "[virtual fs sftp]", errors, Protocol.SFTP, storageType)
    except:
        errors.append("error in fs sftp")
    # no tests vor virtual FS with FTP because of issues with change-dir with curl
    #testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_VIRTUAL_FS,  "[virtual fs  ftp]", errors, Protocol.FTP, storageType)
    # same curl issue prevents creation of dirs -> read only tests, no scp upload
    #scpUpload(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_FS, "[virtual fs  scp]", errors)
    try:
        scpDownload(DEFAULT_PATH_VIRTUAL_FS, "[virtual fs  scp]", errors)
    except:
        errors.append("error in fs scp")

    try:
        testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_ROOT, "[virtual root sftp]", errors, Protocol.SFTP, storageType)
    except:
        errors.append("error in root sftp")
    try:
        testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_VIRTUAL_ROOT,  "[virtual root  ftp]", errors, Protocol.FTP, storageType)
    except:
        errors.append("error in root ftp")
    # no scp for root, see above
    #scpUpload(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_ROOT, "[virtual root  scp]", errors)
    #scpDownload(DEFAULT_PATH_VIRTUAL_ROOT, "[virtual root  scp]", errors)

    testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_SAF, "[virtual saf sftp]", errors, Protocol.SFTP, storageType)
    testCycleReadOnly(BASE_URL_FTP, DEFAULT_PATH_VIRTUAL_SAF,  "[virtual saf  ftp]", errors, Protocol.FTP, storageType)
    # no scp upload for virtual with curl, see above
    #scpUpload(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_SAF, "[virtual saf  scp]", errors)
    scpDownload(DEFAULT_PATH_VIRTUAL_SAF, "[virtual saf  scp]", errors)

    # no RoSAF due to issues with SAF-API
    #testCycleReadOnly(BASE_URL_SFTP, DEFAULT_PATH_VIRTUAL_ROSAF, "[virtual SAFRO sftp]", errors, Protocol.SFTP, storageType)
    #testCycleReadOnly(BASE_URL__FTP, DEFAULT_PATH_VIRTUAL_ROSAF,  "[virtual SAFRO  ftp]", errors, Protocol.FTP, storageType)
    #scpDownload(DEFAULT_PATH_VIRTUAL_ROSAF, "[virtual SAFRO  scp]", errors)

    testKeys(BASE_URL_SFTP + DEFAULT_PATH_VIRTUAL_FS, errors)


# print result
print("\n")
print("\n")
print("\n")
if len(errors) > 0:
    print("***************************** errors *****************************")
    for error in errors:
        print(error)
else:
    print("***************************** no errors *****************************")
print("\n")
print("\n")
print("\n")
