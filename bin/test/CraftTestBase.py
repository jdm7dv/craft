import os
import tempfile
import unittest

import CraftConfig
import CraftStandardDirs
from CraftCore import CraftCore
import InstallDB

class CraftTestBase(unittest.TestCase):
    def setUp(self):
        CraftCore.debug.setVerbose(1)
        self.kdeRoot = tempfile.TemporaryDirectory()
        craftRoot = os.path.normpath(os.path.join(os.path.split(__file__)[0], "..", "..", ".."))
        oldSettings = CraftCore.settings
        CraftCore.settings = CraftConfig.CraftConfig(os.path.join(craftRoot, "craft", "CraftSettings.ini.template"))
        CraftCore.standardDirs = CraftStandardDirs.CraftStandardDirs()
        CraftStandardDirs.CraftStandardDirs.allowShortpaths(False)
        CraftCore.settings.set("Blueprints", "Locations", oldSettings.get("Blueprints", "Locations"))
        CraftCore.settings.set("Blueprints", "BlueprintRoot", oldSettings.get("Blueprints", "BlueprintRoot"))
        CraftCore.settings.set("Compile", "BuildType", "RelWithDebInfo")
        if hasattr(InstallDB, "installdb"):
            del InstallDB.installdb
        InstallDB.installdb = InstallDB.InstallDB(os.path.join(self.kdeRoot.name, "test.db"))

    def tearDown(self):
        InstallDB.installdb.connection.close()
        del InstallDB.installdb
        del self.kdeRoot
