import sys
import optparse
from zutils import Zotonic, errorMsg

def main():
    parser = optparse.OptionParser()
    parser.add_option("-r", "--revision", help="Which revision to backport", default=None)
    parser.add_option("-y", "--yes", help="Do not ask for confirmation", action='store_true')
    parser.add_option("-n", "--pretend", help="Only pretend to backport", action='store_true')
 
    opts, branches = parser.parse_args()

    z = Zotonic()
    
    invalid = [b for b in branches if b not in z.releaseBranches]
    if invalid:
        errorMsg("Invalid branches: " + ", ".join(invalid))

    if z.getCurrentBranch() != "master":
        errorMsg("You need to be on the master branch.")

    if not len(branches):
        branches = [z.latestReleaseBranch]

    if opts.revision:
        log = z.gitCmd("log --pretty=oneline -1 %s" % opts.revision)
    else:
        log = z.gitCmd("log --pretty=oneline -1")

    revision, summary = log.strip().split(" ", 1)

    print "Will backport revision %s to release %s" % (revision, ", ".join(branches))
    print "(%s)" % summary
    print 

    if opts.pretend:
        return

    if not opts.yes:
        print "Press [enter] to perform the backport."
        sys.stdin.readline()

    for b in branches:
        if b not in z.releaseBranches:
            errorMsg("Non-existing branch: "+b)
        target = "release-%s" % b
        z.gitCmd("checkout "+target)
        z.gitCmd("merge origin/"+target)
        z.gitCmd("cherry-pick -x " + revision)

    z.gitCmd("checkout master")
    print "Backport OK."
