# -*- coding: utf-8 -*-
import info
from Package.CMakePackageBase import *

class subinfo(info.infoclass):
    def setTargets( self ):
        for i in ( '0.18.0', '0.18.1', '0.18.2', '0.20.3' ):
            self.targets[ i ] = 'http://poppler.freedesktop.org/poppler-%s.tar.gz' % i
            self.targetInstSrc[ i ] = 'poppler-%s' % i
        self.svnTargets['gitHEAD'] = "git://git.freedesktop.org/git/poppler/poppler|master"
        self.svnTargets['0.18-branch'] = "git://git.freedesktop.org/git/poppler/poppler|poppler-0.18"
        self.svnTargets['0.20-branch'] = "git://git.freedesktop.org/git/poppler/poppler|poppler-0.20"

        self.shortDescription = "PDF rendering library based on xpdf-3.0"
        self.defaultTarget = "0.18.2"

    def setDependencies( self ):
        self.dependencies['win32libs-bin/freetype'] = 'default'
        self.dependencies['win32libs-bin/openjpeg'] = 'default'
        self.dependencies['win32libs-bin/lcms'] = 'default'
        self.dependencies['win32libs-bin/zlib'] = 'default'
        self.dependencies['win32libs-bin/jpeg'] = 'default'
        self.dependencies['win32libs-bin/libpng'] = 'default'
        self.dependencies['win32libs-bin/libxml2'] = 'default'
        self.runtimeDependencies['data/poppler-data'] = 'default'
        self.dependencies['libs/qt'] = 'default'

class Package(CMakePackageBase):
    def __init__( self, **args ):
        self.subinfo = subinfo()
        CMakePackageBase.__init__( self )

        self.subinfo.options.package.packageName = 'poppler'
        self.subinfo.options.configure.defines = "-DBUILD_QT4_TESTS=ON -DENABLE_XPDF_HEADERS=ON"

if __name__ == '__main__':
    Package().execute()
