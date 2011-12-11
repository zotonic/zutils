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
        if os.path.exists("bin/zotonic"):
            executable = "bin/zotonic"
        else:
            executable = "zotonic"
        self.basedir = cmdOutput("echo $(dirname $(dirname $(dirname `%s sitedir t`)))" % executable).strip()
        self.versions = sorted(self.gitCmd("tag|grep ^release|awk '{print $1}'|awk -F- '{print $2}'").strip().split("\n"))[::-1]
        self.releaseBranches = sorted(self.gitCmd("branch|grep ^..release|awk '{print $1}'|awk -F- '{print $2}'").strip().split("\n"))[::-1]


    def gitCmd(self, cmd):
        return cmdOutput("git --work-tree=%s %s" % (self.basedir, cmd))

    @property
    def latestReleaseBranch(self):
        return self.releaseBranches[0]

    def latestVersion(self, releaseBranch=None):
        if not releaseBranch:
            releaseBranch = self.latestReleaseBranch
        prefix = re.sub("\.x", ".", releaseBranch)
        return [v for v in self.versions if v[:len(prefix)] == prefix][0]

    def nextVersion(self, releaseBranch=None):
        if not releaseBranch:
            releaseBranch = self.latestReleaseBranch
        return Version(self.latestVersion(releaseBranch)).next


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


    def printLog(self, buf, version):
        frm, to = self.calcLog(version)
        buf.write(self.gitCmd("shortlog %s..%s" % (frm, to)))


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
