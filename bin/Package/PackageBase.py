#
# copyright (c) 2009 Ralf Habacker <ralf.habacker@freenet.de>
#
from CraftBase import *
from CraftCompiler import *
from InstallDB import *
from Blueprints.CraftPackageObject import *
from Utils import CraftHash, GetFiles, CraftChoicePrompt
from Utils.CraftManifest import CraftManifest

import json

class PackageBase(CraftBase):
    """
     provides a generic interface for packages and implements the basic stuff for all
     packages
    """

    # uses the following instance variables
    # todo: place in related ...Base

    # rootdir    -> CraftBase
    # package    -> PackageBase
    # force      -> PackageBase
    # category   -> PackageBase
    # version    -> PackageBase
    # packagedir -> PackageBase
    # imagedir   -> PackageBase

    def __init__(self):
        CraftCore.log.debug("PackageBase.__init__ called")
        CraftBase.__init__(self)

    def qmerge(self):
        """mergeing the imagedirectory into the filesystem"""
        ## \todo is this the optimal place for creating the post install scripts ?

        if self.package.isInstalled:
            self.unmerge()

        copiedFiles = []  # will be populated by the next call
        if not utils.copyDir(self.imageDir(), CraftCore.standardDirs.craftRoot(), copiedFiles=copiedFiles):
            return False

        # add package to installed database -> is this not the task of the manifest files ?

        revision = self.sourceRevision()
        package = CraftCore.installdb.addInstalled(self.package, self.version, revision=revision)
        fileList = self.getFileListFromDirectory(CraftCore.standardDirs.craftRoot(), copiedFiles)
        package.addFiles(fileList)
        package.install()

        if (CraftCore.settings.getboolean("Packager", "CreateCache") or
            CraftCore.settings.getboolean("Packager", "UseCache")):
            package.setCacheVersion(self.cacheVersion())

        return True

    def unmerge(self):
        """unmergeing the files from the filesystem"""
        CraftCore.log.debug("Packagebase unmerge called")
        packageList = CraftCore.installdb.getInstalledPackages(self.package)
        for package in packageList:
            fileList = package.getFilesWithHashes()
            self.unmergeFileList(CraftCore.standardDirs.craftRoot(), fileList)
            package.uninstall()
        return True

    def strip(self, fileName, symbolDest=None):
        """strip debugging informations from shared libraries and executables - mingw only!!! """
        if self.subinfo.options.package.disableStriping or CraftCore.compiler.isMSVC() or not CraftCore.compiler.isGCCLike():
            CraftCore.log.warning(f"Skipping stripping of {fileName} -- either disabled or unsupported with this compiler")
            return True

        if OsUtils.isMac():
            CraftCore.log.debug(f"Skipping stripping of files on macOS -- not implemented")
            return True

        if os.path.isabs(fileName):
            filepath = fileName
        else:
            CraftCore.log.warning("Please pass an absolute file path to strip")
            basepath = os.path.join(self.installDir())
            filepath = os.path.join(basepath, "bin", fileName)
        if not symbolDest:
            return utils.system(["strip", "-s", filepath])
        else:
            symFile = os.path.join(symbolDest, f"{os.path.basename(filepath)}.sym")
            return (utils.system(["objcopy", "--only-keep-debug", filepath, symFile]) and
                    utils.system(["strip", "--strip-debug", "--strip-unneeded", filepath]) and
                    utils.system(["objcopy", "--add-gnu-debuglink", symFile, filepath]))

    def createImportLibs(self, pkgName):
        """create the import libraries for the other compiler(if ANSI-C libs)"""
        basepath = os.path.join(self.installDir())
        utils.createImportLibs(pkgName, basepath)

    def printFiles(self):
        packageList = CraftCore.installdb.getInstalledPackages(self.package)
        for package in packageList:
            fileList = package.getFiles()
            fileList.sort()
            for file in fileList:
                print(file[0])
        return True

    def getAction(self, cmd=None):
        if not cmd:
            command = sys.argv[1]
            options = None
            #            print sys.argv
            if (len(sys.argv) > 2):
                options = sys.argv[2:]
        else:
            command = cmd
            options = None
        # \todo options are not passed through by craft.py fix it
        return [command, options]

    def execute(self, cmd=None):
        """called to run the derived class
        this will be executed from the package if the package is started on its own
        it shouldn't be called if the package is imported as a python module"""

        CraftCore.log.debug("PackageBase.execute called. args: %s" % sys.argv)
        command, _ = self.getAction(cmd)

        return self.runAction(command)

    def fetchBinary(self, downloadRetriesLeft=3) -> bool:
        if self.subinfo.options.package.disableBinaryCache:
            return False

        for url in [self.cacheLocation()] + self.cacheRepositoryUrls():
            CraftCore.log.debug(f"Trying to restore {self} from cache: {url}.")
            if url == self.cacheLocation():
                fileUrl = f"{url}/manifest.json"
                if os.path.exists(fileUrl):
                    with open(fileUrl, "rt", encoding="UTF-8") as f:
                        manifest = CraftManifest.fromJson(json.load(f))
                else:
                    continue
            else:
                manifest = CraftManifest.fromJson(CraftCore.cache.cacheJsonFromUrl(f"{url}/manifest.json"))
            fileEntry = manifest.get(str(self)).files
            files = []
            for f in fileEntry:
                if f.version == self.version:
                    files.append(f)
            latest = None
            if not files:
                CraftCore.log.debug(f"Could not find {self}={self.version} in {url}")
                continue
            latest = files[0]

            if url != self.cacheLocation():
                downloadFolder = self.cacheLocation(os.path.join(CraftCore.standardDirs.downloadDir(), "cache"))
            else:
                downloadFolder = self.cacheLocation()
            localArchiveAbsPath = OsUtils.toNativePath(os.path.join(downloadFolder, latest.fileName))
            localArchivePath, localArchiveName = os.path.split(localArchiveAbsPath)


            if url != self.cacheLocation():
                if not os.path.exists(localArchiveAbsPath):
                    os.makedirs(localArchivePath, exist_ok=True)
                    fUrl = f"{url}/{latest.fileName}"
                    if not GetFiles.getFile(fUrl, localArchivePath, localArchiveName):
                        CraftCore.log.warning(f"Failed to fetch {fUrl}")
                        return False
            elif not os.path.isfile(localArchiveAbsPath):
                continue

            if not CraftHash.checkFilesDigests(localArchivePath, [localArchiveName],
                                               digests=latest.checksum,
                                               digestAlgorithm=CraftHash.HashAlgorithm.SHA256):
                CraftCore.log.warning(f"Hash did not match, {localArchiveName} might be corrupted")
                if downloadRetriesLeft and CraftChoicePrompt.promptForChoice("Do you want to delete the files and redownload them?",
                                                     [("Yes", True), ("No", False)],
                                                     default="Yes"):
                    return utils.deleteFile(localArchiveAbsPath) and self.fetchBinary(downloadRetriesLeft=downloadRetriesLeft-1)
                return False
            self.subinfo.buildPrefix = latest.buildPrefix
            self.subinfo.isCachedBuild = True
            if not (self.cleanImage()
                    and utils.unpackFile(localArchivePath, localArchiveName, self.imageDir())
                    and self.internalPostInstall()
                    and self.postInstall()
                    and self.qmerge()
                    and self.internalPostQmerge()
                    and self.postQmerge()):
                return False
            return True
        return False

    @staticmethod
    def getFileListFromDirectory(imagedir, filePaths):
        """ create a file list containing hashes """
        ret = []

        algorithm = CraftHash.HashAlgorithm.SHA256
        for filePath in filePaths:
            relativeFilePath = os.path.relpath(filePath, imagedir)
            digest = algorithm.stringPrefix() + CraftHash.digestFile(filePath, algorithm)
            ret.append((relativeFilePath, digest))
        return ret

    @staticmethod
    def unmergeFileList(rootdir, fileList):
        """ delete files in the fileList if has matches """
        for filename, filehash in fileList:
            fullPath = os.path.join(rootdir, os.path.normcase(filename))
            if os.path.isfile(fullPath) or os.path.islink(fullPath):
                if filehash:
                    algorithm = CraftHash.HashAlgorithm.getAlgorithmFromPrefix(filehash)
                    currentHash = algorithm.stringPrefix() + CraftHash.digestFile(fullPath, algorithm)
                if not filehash or currentHash == filehash:
                    OsUtils.rm(fullPath, True)
                else:
                    CraftCore.log.warning(
                        f"We can't remove {fullPath} as its hash has changed,"
                        f" that usually implies that the file was modified or replaced")
            elif not os.path.isdir(fullPath) and os.path.lexists(fullPath):
                CraftCore.log.debug(f"Remove a dead symlink {fullPath}")
                OsUtils.rm(fullPath, True)
            elif not os.path.isdir(fullPath):
                CraftCore.log.warning("file %s does not exist" % fullPath)

            containingDir = os.path.dirname(fullPath)
            if os.path.exists(containingDir) and not os.listdir(containingDir):
                CraftCore.log.debug(f"Delete empty dir {containingDir}")
                utils.rmtree(containingDir)


    def runAction(self, command):
        functions = {"fetch": "fetch",
                     "cleanimage": "cleanImage",
                     "cleanbuild": "cleanBuild",
                     "unpack": "unpack",
                     "compile": "compile",
                     "configure": "configure",
                     "make": "make",
                     "install": ["install", "internalPostInstall"],
                     "post-install": "postInstall",
                     "test": "unittest",
                     "qmerge": ["qmerge", "internalPostQmerge"],
                     "post-qmerge": "postQmerge",
                     "unmerge": "unmerge",
                     "package": "createPackage",
                     "createpatch": "createPatch",
                     "print-files": "printFiles",
                     "checkdigest": "checkDigest",
                     "fetch-binary": "fetchBinary"}
        if command in functions:
            try:
                steps = functions[command]
                if not isinstance(steps, list):
                    steps = [steps]
                for step in steps:
                    if not getattr(self, step)():
                        return False
            except AttributeError as e:
                raise BlueprintException(str(e), self.package, e)

        else:
            CraftCore.log.error("command %s not understood" % command)
            return False
        return True
