import base
import utils
import sys
import info

class subinfo(info.infoclass):
    def setDependencies( self ):
        self.hardDependencies['virtual/base'] = 'default'
        self.hardDependencies['libs/qt'] = 'default'
        self.hardDependencies['win32libs-bin/openssl'] = 'default'

    def setTargets( self ):
        self.svnTargets['2.0.0-5'] = 'tags/qca/2.0.0'
        self.svnTargets['2.0.1-3'] = 'tags/qca/2.0.1'
        self.svnTargets['svnHEAD'] = 'trunk/kdesupport/qca'
        for i in ['4.3.0', '4.3.1', '4.3.2', '4.3.3', '4.3.4', '4.3']:
            self.svnTargets[ i ] = 'tags/kdesupport-for-4.3/kdesupport/qca'
        self.defaultTarget = 'svnHEAD'

class subclass(base.baseclass):
    def __init__( self, **args ):
        base.baseclass.__init__( self, args=args )
        self.instsrcdir = "qca"
        self.subinfo = subinfo()

    def unpack( self ):
        return self.kdeSvnUnpack()

    def compile( self ):
        return self.kdeCompile()

    def install( self ):
        return self.kdeInstall()

    def make_package( self ):
        if self.buildTarget == "svnHEAD":
            return self.doPackaging( "qca" )
        else:
            return self.doPackaging( "qca", self.buildTarget, True )
if __name__ == '__main__':
    subclass().execute()
