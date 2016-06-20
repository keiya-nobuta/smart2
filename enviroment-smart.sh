#!/bin/sh
# This sctript suits prm packages that created by Yocto.

TARGET_ROOTFS=$1
PKGS_DIR=$2

#Check the parameters
if [ -z "$2" -o $1 = "--help" -o $1 = "-h" -o $1 = "-H" ]; then
    echo ""
    echo "usage:     \$ . enviroment-smart.sh rootfs_dir packages_dir "
    echo "Add channels from the sources in packages_dir,and build the enviroment for target rootfs directory."
    echo ""
    echo "#For example"
    echo "If you have packages of target(e.g. x86 packages created by Yocto):"
    echo "     \$ ls /home/test/x86_rpm/"
    echo "     all  i586  qemux86"
    echo "And you want to manage(e.g. install/remove/search) these packages on your host machain."
    echo "First, you should use the following command to set up your smart environment"
    echo "     \$ . enviroment-smart.sh /home/test/x86_rootfs /home/test/x86_rpm "
    echo "Then, you can manange target packages for target rootfs:"
    echo "     \$ smart --rootfs-dir=/home/test/x86-rootfs install pkgname"
    echo "     \$ smart --rootfs-dir=/home/test/x86-rootfs remove pkgname"
    echo "     \$ smart --rootfs-dir=/home/test/x86-rootfs query '*kgnam*'"
    echo "Or cutomize your rootfs:"
    echo "     \$ smart --rootfs-dir=/home/test/x86-rootfs --interface=tgui"
    echo ""
    echo "Note"
    echo "Smart mananges packages by repodate, make sure your repodate is correct with your packages."
    echo "    \$ ls /home/test/x86_rpm/all/repodata"
    echo "       filelists.xml.gz  other.xml.gz  primary.xml.gz  repomd.xml"
    exit 0
fi

if [ ! -d $PKGS_DIR ]; then
    echo " Error!  The packages_dir is not exist: $PKGS_DIR . Please check. "
    exit 1
fi

if [ ! -d $TARGET_ROOTFS ]; then
    echo " $TARGET_ROOTFS is not exist. mkdir $TARGET_ROOTFS. "
    mkdir -p $TARGET_ROOTFS
fi

# Pseudo Environment
export LD_LIBRARY_PATH=$OECORE_NATIVE_SYSROOT/usr/bin/../lib/pseudo/lib:$OECORE_NATIVE_SYSROOT/usr/bin/../lib/pseudo/lib64
export LD_PRELOAD=libpseudo.so
export PSEUDO_PASSWD=$TARGET_ROOTFS
export PSEUDO_OPTS=
export PSEUDO_LIBDIR=$OECORE_NATIVE_SYSROOT/usr/bin/../lib/pseudo/lib64
export PSEUDO_NOSYMLINKEXP=1
export PSEUDO_DISABLED=0
export PSEUDO_PREFIX=$OECORE_NATIVE_SYSROOT/usr
export PSEUDO_LOCALSTATEDIR=`pwd`/pseudo/
#Create a initial passwd file for smart.
if [ ! -d $TARGET_ROOTFS/etc ]; then
    mkdir $TARGET_ROOTFS/etc
fi

cat << EOF > $TARGET_ROOTFS/etc/passwd
root::0:0:root:/home/root:/bin/sh
daemon:*:1:1:daemon:/usr/sbin:/bin/sh
bin:*:2:2:bin:/bin:/bin/sh
sys:*:3:3:sys:/dev:/bin/sh
sync:*:4:65534:sync:/bin:/bin/sync
games:*:5:60:games:/usr/games:/bin/sh
man:*:6:12:man:/var/cache/man:/bin/sh
lp:*:7:7:lp:/var/spool/lpd:/bin/sh
mail:*:8:8:mail:/var/mail:/bin/sh
news:*:9:9:news:/var/spool/news:/bin/sh
uucp:*:10:10:uucp:/var/spool/uucp:/bin/sh
proxy:*:13:13:proxy:/bin:/bin/sh
www-data:*:33:33:www-data:/var/www:/bin/sh
backup:*:34:34:backup:/var/backups:/bin/sh
list:*:38:38:Mailing List Manager:/var/list:/bin/sh
irc:*:39:39:ircd:/var/run/ircd:/bin/sh
gnats:*:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh
nobody:*:65534:65534:nobody:/nonexistent:/bin/sh
EOF
#In general,the initial passwd file comes from base-passwd-update pacakage
#So try to get the passwd from base-passwd-update pacakage
default_pwd_path=`find $PKGS_DIR -name "base-passwd-update*"`
echo "Find default_pwd_path = $default_pwd_path"
 
if [ "${default_pwd_path}x" != "x" ]; then
    echo "find result : `echo "$default_pwd_path" | wc -l`"
    if [ `echo "$default_pwd_path" | wc -l` != "1" ];then
        echo "there are more base-passwd-updatesd packages. \ Can't decide which one should be used. \ So use the default passwd file"
    else
        base_passwd_tmp_dir="base-passwd-updatesd.temp"
        mkdir $base_passwd_tmp_dir
        cp $default_pwd_path $base_passwd_tmp_dir/
        cd $base_passwd_tmp_dir
        rpm2cpio ${default_pwd_path} | cpio -idu
        echo "find ${default_pwd_path}!!"
        cd ..
        cp -f ${base_passwd_tmp_dir}/usr/share/base-passwd/passwd.master $TARGET_ROOTFS/etc/passwd
        rm -rf ${base_passwd_tmp_dir}
    fi
fi

DEF_PRIORITY=1
RPM_VERSION=5
SMART="smart --log-level=error --data-dir=$TARGET_ROOTFS/var/lib/smart"
RPM=rpm
rpm_libdir=$TARGET_ROOTFS"/var/lib/rpm"

echo "Configuring RPM DB settings" 
rm -rf $rpm_libdir/
mkdir -p $rpm_libdir/log
touch $rpm_libdir/log/log.0000000001

cat << EOF > $rpm_libdir/DB_CONFIG
# ================ Environment\n
set_data_dir .
set_create_dir .
set_lg_dir ./log
set_tmp_dir ./tmp
set_flags db_log_autoremove on

# -- thread_count must be >= 8
set_thread_count 64

# ================ Logging

# ================ Memory Pool
set_cachesize 0 1048576 0
set_mp_mmapsize 268435456

# ================ Locking
set_lk_max_locks 16384
set_lk_max_lockers 16384
set_lk_max_objects 16384
mutex_set_max 163840

# ================ Replication
EOF

opt="-qa" 
if [ "$RPM_VERSION" = "4" ]; then
        opt="--initdb" 
fi

$RPM --root $TARGET_ROOTFS  --dbpath /var/lib/rpm $opt > /dev/null
if [ "$?" != "0" ]; then
        echo "Create rpm database failed." 
        exit 1
fi

# RPM_SIGN_PACKAGES setting be ignored
echo "Configuring Smart settings" 
rm -rf $TARGET_ROOTFS/var/lib/smart
$SMART config --set rpm-root="$TARGET_ROOTFS" 
$SMART config --set rpm-dbpath="/var/lib/rpm" 
$SMART config --set rpm-extra-macros._var="/var" 
$SMART config --set rpm-extra-macros._tmppath=/oe_install/tmp

# RPM_PREFER_ELF_ARCH setting be ignored
$SMART config --set rpm-ignoresize=1
$SMART config --set rpm-nolinktos=1
$SMART config --set rpm-noparentdirs=1

# RPM_CHECK_SIGNATURES setting be ignored
# BAD_RECOMMENDATIONS setting be ignored
# NO_RECOMMENDATIONS setting be ignored
# PACKAGE_EXCLUDE setting be ignored

# Create channels
DISTRO_ARCHS=$(ls -l $PKGS_DIR | awk '/^d/{print $NF}')
for arch in $DISTRO_ARCHS; do
        echo "Adding Smart channel $arch" 
        $SMART channel --add $arch type=rpm-md baseurl="$PKGS_DIR/$arch" -y
        #echo $?
        $SMART channel --set $arch priority=$DEF_PRIORITY
done

echo "Adding Smart RPM DB channel" 
$SMART channel --add rpmsys type=rpm-sys -y

# Construct install scriptlet wrapper
echo "Configuring RPM cross-install scriptlet_wrapper" 
if [ $RPM_VERSION = '4' ]; then
        scriptletcmd="\$2 \$3 \$4" 
        scriptpath="\$3" 
else
        scriptletcmd="\$2 \$1/\$3 \$4" 
        scriptpath="\$1/\$3" 
fi
WORKDIR=${PKGS_DIR}
cat << EOF > $WORKDIR/scriptlet_wrapper
#!/bin/bash

export PATH=$PATH
export D=$TARGET_ROOTFS
export OFFLINE_ROOT="\$D" 
export IPKG_OFFLINE_ROOT="\$D" 
export OPKG_OFFLINE_ROOT="\$D" 
export INTERCEPT_DIR=$WORKDIR/intercept_scripts
export NATIVE_ROOT=$OECORE_NATIVE_SYSROOT

echo "$scriptletcmd" 

$scriptletcmd
if [ \$? -ne 0 ]; then
        if [ \$4 -eq 1 ]; then
                mkdir -p \$1/etc/rpm-postinsts
                num=100
                while [ -e \$1/etc/rpm-postinsts/\${num}-* ]; do num=\$((num + 1)); done
                name=\`head -1 $scriptpath | cut -d' ' -f 2\`
                echo "#!\$2" > \$1/etc/rpm-postinsts/\${num}-\${name}
                echo "# Arg: \$4" >> \$1/etc/rpm-postinsts/\${num}-\${name}
                cat $scriptpath >> \$1/etc/rpm-postinsts/\${num}-\${name}
                chmod +x \$1/etc/rpm-postinsts/\${num}-\${name}
        else
                echo "Error: pre/post remove scriptlet failed" 
        fi
fi

EOF

chmod 0755 $WORKDIR/scriptlet_wrapper
$SMART config --set rpm-extra-macros._cross_scriptlet_wrapper="$WORKDIR/scriptlet_wrapper" 
#echo $?
$SMART config --show
#echo $?
echo "$SMART config --show" 

#$SMART clean
echo "$SMART search busybox"
$SMART search busybox
