import os
import sys
import optparse
from zutils import Zotonic, errorMsg


def main():
    parser = optparse.OptionParser()
    parser.add_option("-r", "--revision", help="Which revision to backport", default=None)
    parser.add_option("-n", "--pretend", help="Only pretend to backport", action='store_true')
 
    opts, branches = parser.parse_args()

    z = Zotonic()

    if z.getCurrentBranch() != "default":
        errorMsg("You need to be on the default branch.")

    if not len(branches):
        branches = [z.latestReleaseBranch]

    if opts.revision:
        log = z.hgCmd("log -r %s" % opts.revision)
    else:
        log = z.hgCmd("parents")

    log = z.log2dict(log)

    print "Will backport revision %s to %s" % (log['revision'], ", ".join(branches))
    print "(%s)" % log['summary']
    print 

    if opts.pretend:
        return

    z.hgCmd("export %s > /tmp/%s.patch" % (log['revision'], log['revision']))

    for b in branches:
        if b not in z.releaseBranches:
            errorMsg("Non-existing branch: "+b)
        target = "release-%s" % b
        z.hgCmd("update "+target)
        msg = "Backport to %s from r%s: %s" % (b, log['revision'], log['summary'])
        z.hgCmd("import -m \"%s\" /tmp/%s.patch" % (msg, log['revision']))

    z.hgCmd("update default")
    print "Backport OK."
