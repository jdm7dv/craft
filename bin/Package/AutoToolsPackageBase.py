#
# copyright (c) 2010 Ralf Habacker <ralf.habacker@freenet.de>
#
import CraftDebug
from Package.PackageBase import *
from Source.MultiSource import *
from BuildSystem.AutoToolsBuildSystem import *
from Packager.TypePackager import *

class AutoToolsPackageBase (PackageBase, MultiSource, AutoToolsBuildSystem, TypePackager):
    """provides a base class for autotools based packages from any source"""
    def __init__(self):
        CraftDebug.debug("AutoToolsPackageBase.__init__ called", 2)
        PackageBase.__init__(self)
        MultiSource.__init__(self)
        AutoToolsBuildSystem.__init__(self)
        TypePackager.__init__(self)
        #needed to run autogen sh, this is needed in all checkouts but normaly not in a tarball
        if self.subinfo.hasSvnTarget():
            self.subinfo.options.configure.bootstrap = True
