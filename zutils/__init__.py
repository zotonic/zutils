import os, sys, re
from distutils.version import LooseVersion


def errorMsg(msg):
    sys.stderr.write("** %s\n\n" % msg)
    exit(1)


def cmdOutput(cmd):
    return os.popen(cmd, "r").read()


class Zotonic(object):
    """ Utility class representing a zotonic working copy. """

    def __init__(self):
        if os.path.exists("bin/zotonic"):
            executable = "bin/zotonic"
        else:
            executable = "zotonic"
        self.basedir = cmdOutput("echo $(dirname $(dirname $(dirname `%s sitedir t`)))" % executable).strip()
        self.versions = self.hgCmd("tags|grep ^release|awk '{print $1}'|awk -F- '{print $2}'").strip().split("\n")
        self.releaseBranches = self.hgCmd("branches|grep ^release|awk '{print $1}'|awk -F- '{print $2}'").strip().split("\n")


    def hgCmd(self, cmd):
        return cmdOutput("hg -R %s %s" % (self.basedir, cmd))

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


    def getLog(self, version):
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

        log = self.hgCmd("log -b %s -r %s:%s" % (branch, frm, to))

        log = [self.log2dict(s) for s in log.strip().split("\n\n")]
        return log


    def log2dict(self, msg):
        d = dict([re.split(":\s+", l.strip(), 1) for l in msg.split("\n") if l.strip()])
        d['revision'],d['revision_hash'] = d['changeset'].split(':')
        return d


    def printLog(self, buf, version):
        from collections import defaultdict
        by_author = defaultdict(list)

        for l in self.getLog(version):
            author = l['user'].split(" ")[0]
            by_author[author].append(l)

        for author in by_author.keys():
            buf.write(author+"\n")
            buf.write("-" * len(author)+"\n")
            buf.write("\n")
            for l in by_author[author]:
                buf.write(" * %s" % l['summary']+"\n")
            buf.write("\n")


    def getCurrentBranch(self):
        return self.hgCmd("branch").strip()



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
