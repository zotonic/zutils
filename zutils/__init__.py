import os, sys, re
from distutils.version import LooseVersion


def errorMsg(msg):
    sys.stderr.write("** %s\n\n" % msg)
    exit(1)


def cmdOutput(cmd):
    return os.popen(cmd, "r").read()


class Zotonic(object):
    """ Utility class representing a Zotonic working copy. """

    def __init__(self):
        self.basedir = os.getcwd()
        if not os.path.exists(os.path.join(self.basedir, "bin/zotonic")):
            errorMsg("You need to run this command from the Zotonic root dir.")
        self.versions = sorted([Version(v) for v in self.gitCmd("tag|grep ^release-|awk '{print $1}'|awk -F- '{print $2}'|grep -v '[0-9]p[0-9]'").strip().split("\n")])[::-1]
        self.releaseBranches = sorted(self.gitCmd("branch|grep ^..release|awk -F- '{print $2}'").strip().split("\n"))[::-1]


    def gitCmd(self, cmd):
        return cmdOutput("git --work-tree=%s %s" % (self.basedir, cmd))

    @property
    def currentBranch(self):
        return self.gitCmd("rev-parse --abbrev-ref HEAD").strip().replace("release-", "")

    @property
    def latestReleaseBranch(self):
        return self.versions[0].featureversion

    def latestVersion(self, releaseBranch=None):
        if not releaseBranch:
            releaseBranch = self.latestReleaseBranch
        prefix = re.sub("\.x", ".", releaseBranch)
        return [v for v in self.versions if str(v)[:len(prefix)] == prefix][0]

    def nextVersion(self, releaseBranch=None):
        if not releaseBranch:
            releaseBranch = self.latestReleaseBranch
        return self.latestVersion(releaseBranch).next


    def calcLog(self, version):
        # check if there is a next version
        v = Version(version)

        branch = "release-%s" % v.featureversion

        if v.featureversion not in self.releaseBranches:
            raise Exception("Branch not found: " + branch)

        if v.prev not in self.versions:
            raise Exception("Version tag not found: " + v.prev)
        frm = "release-%s" % v.prev

        if str(v) not in self.versions:
            to = "release-%s" % v.featureversion
        else:
            to = "release-%s" % v

        return (frm, to)


    def _fmtLog(self, log):
        log = log.replace("      * ", "* ")
        log = log.replace(':\n', ':\n\n')
        log = re.sub(' \(cherry picked.*?\)', '', log)
        return log
        
    def printLog(self, buf, version):
        frm, to = self.calcLog(version)
        buf.write(self._fmtLog(self.gitCmd("shortlog --format=\"* %%s\" %s..%s" % (frm, to))))
        

    def printFeatureLog(self, buf, releaseBranch=None):
        if not releaseBranch:
            releaseBranch = self.latestReleaseBranch
        buf.write(self._fmtLog(self.gitCmd("shortlog --format=\"* %%s\" release-%s..%s" % (releaseBranch, "master"))))
        

    def getCurrentBranch(self):
        return self.gitCmd("name-rev --name-only HEAD").strip()



class Version(LooseVersion):
    @property
    def prev(self):
        version = list(self.version)
        version[-1] = int(version[-1]) -1
        if version[-1] < 0:
            raise Exception("Invalid version for prev()")
        return '.'.join([str(part) for part in version])

    @property
    def next(self):
        version = list(self.version)
        version[-1] = int(version[-1]) +1
        return '.'.join([str(part) for part in version])

    @property
    def featureversion(self):
        version = list(self.version)[:-1]
        return '.'.join([str(part) for part in version])+".x"


