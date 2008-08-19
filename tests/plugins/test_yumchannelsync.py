import os

try:
    from smart.plugins.yumchannelsync import syncYumRepos, BASEARCH, RELEASEVER
except ImportError: # yum (rpmUtils.arch) not available
    syncYumRepos = None
from smart import sysconf

from tests.mocker import MockerTestCase


FEDORA_BASE_REPO = """\
[base]
name=Fedora 8 - i386 - Base
baseurl=http://mirrors.kernel.org/fedora/releases/8/Everything/i386/os/
enabled=1
gpgcheck=1
"""

FEDORA_DEBUG_REPO = """\
[debug]
name=Fedora 8 - i386 - Debug
baseurl=http://mirrors.kernel.org/fedora/releases/8/Everything/i386/debug/
enabled=0
gpgcheck=1
"""

FEDORA_DYNAMIC_REPO = """\
[fedora]
name=Fedora $releasever - $basearch
failovermethod=priority
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/releases/$releasever/Everything/$basearch/os/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora file:///etc/pki/rpm-gpg/RPM-GPG-KEY
"""

class YumRepoSyncTest(MockerTestCase):

    def setUp(self):
        self.yum_dir = self.makeDir()
        self.repos_dir = os.path.join(self.yum_dir, "yum.repos.d")
        os.mkdir(self.repos_dir)

    def test_synchronize_repos_directory(self):
        if not syncYumRepos:
            self.skip("yum not available")
        self.makeFile(FEDORA_BASE_REPO, dirname=self.repos_dir, basename="fedora-base.repo")
        syncYumRepos(self.repos_dir)
        self.assertEquals(sysconf.get("channels"), {
                          "yumsync-base":
                              {"disabled": False,
                               "type": "rpm-md",
                               "name": "Fedora 8 - i386 - Base",
                               "baseurl": "http://mirrors.kernel.org/fedora/releases/8/Everything/i386/os/"},
                         })


    def test_cleanup_removed_entries(self):
        if not syncYumRepos:
            self.skip("yum not available")
        self.makeFile(FEDORA_BASE_REPO, dirname=self.repos_dir, basename="fedora-base.repo")
        syncYumRepos(self.repos_dir)
        os.unlink(os.path.join(self.repos_dir, "fedora-base.repo"))
        self.makeFile(FEDORA_DEBUG_REPO, dirname=self.repos_dir, basename="fedora-debug.repo")
        syncYumRepos(self.repos_dir)
        self.assertEquals(sysconf.get("channels"), {
                          "yumsync-debug":
                              {"disabled": True,
                               "type": "rpm-md",
                               "name": "Fedora 8 - i386 - Debug",
                               "baseurl": "http://mirrors.kernel.org/fedora/releases/8/Everything/i386/debug/"},
                         })

    def test_synchronize_dynamic_repos(self):
        if not syncYumRepos:
            self.skip("yum not available")
        self.makeFile(FEDORA_DYNAMIC_REPO, dirname=self.repos_dir, basename="fedora.repo")
        syncYumRepos(self.repos_dir)
        self.assertEquals(sysconf.get("channels")["yumsync-fedora"]["name"],
                          "Fedora %s - %s" % (RELEASEVER, BASEARCH))

