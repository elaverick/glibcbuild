%global security_hardening nonow
%define glibc_target_cpu %{_build}
%global __brp_elfperms  /bin/true
%global _gcc_lto_cflags -fno-lto

Summary:        Main C library
Name:           glibc
Version:        %{version}
Release:        1%{?dist}
License:        LGPLv2+
URL:            http://www.gnu.org/software/libc
Group:          Applications/System


Source0: http://ftp.gnu.org/gnu/glibc/%{name}-%{version}.tar.xz
%define sha512 %{name}=9ea0bbda32f83a85b7da0c34f169607fb8a102f0a11a914e6bf531be47d1bef4f5307128286cffa1e2dc5879f0e6ccaef527dd353486883fa332a0b44bde8b3e

Source1:        locale-gen.sh
Source2:        locale-gen.conf

#Patch taken from http://www.linuxfromscratch.org/patches/downloads/glibc/glibc-2.31-fhs-1.patch
Patch0:         glibc-2.31-fhs-1.patch

Provides:       rtld(GNU_HASH)
Provides:       /sbin/ldconfig

Requires:       filesystem
Requires:       %{name}-libs = %{version}-%{release}

Conflicts:      %{name}-i18n < 2.36-4

%define ExtraBuildRequires bison, python3, python3-libs

%description
This library provides the basic routines for allocating memory,
searching directories, opening and closing files, reading and
writing files, string handling, pattern matching, arithmetic,
and so on.

%package libs
Summary:    glibc shared library
Group:      System/Libraries
Conflicts:  %{name} < 2.36-5

%description libs
This subpackage contains the implementation as a shared library.

%package    devel
Summary:    Header files for glibc
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description devel
These are the header files of glibc.

%package    lang
Summary:    Additional language files for glibc
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description lang
These are the additional language files of glibc.

%package    i18n
Summary:    Additional internationalization files for glibc
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description i18n
These are the additional internationalization files of glibc.

%package    iconv
Summary:    gconv modules for glibc
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description iconv
These is gconv modules for iconv() and iconv tools.

%package    tools
Summary:    tools for glibc
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description tools
Extra tools for glibc.

%package    nscd
Summary:    Name Service Cache Daemon
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description nscd
Name Service Cache Daemon

%prep
%autosetup -p1
sed -i 's/\\$$(pwd)/`pwd`/' timezone/Makefile
install -vdm 755 %{_builddir}/%{name}-build
# do not try to explicitly provide GLIBC_PRIVATE versioned libraries
%define __find_provides %{_builddir}/%{name}-%{version}/find_provides.sh
%define __find_requires %{_builddir}/%{name}-%{version}/find_requires.sh

# create find-provides and find-requires script in order to ignore GLIBC_PRIVATE errors
cat > find_provides.sh << _EOF
#! /bin/sh
if [ -d /tools ]; then
  /tools/lib/rpm/find-provides | grep -v GLIBC_PRIVATE
else
  %{_libdir}/rpm/find-provides | grep -v GLIBC_PRIVATE
fi
exit 0
_EOF
chmod +x find_provides.sh

cat > find_requires.sh << _EOF
#! /bin/sh
if [ -d /tools ]; then
  /tools/lib/rpm/find-requires %{buildroot} %{glibc_target_cpu} | grep -v GLIBC_PRIVATE
else
  %{_libdir}/rpm/find-requires %{buildroot} %{glibc_target_cpu} | grep -v GLIBC_PRIVATE
fi
_EOF
chmod +x find_requires.sh

%build

cd %{_builddir}/%{name}-build
../%{name}-%{version}/configure \
        --host=%{_host} --build=%{_build} \
        CFLAGS="%{optflags}  -I/usr/local/include/kernel_headers_%{KERNELVERSION}/usr/include/" \
        CXXFLAGS="%{optflags} -I /usr/local/include/kernel_headers_%{KERNELVERSION}/usr/include/" \
        CPPFLAGS="-fno-lto -I /usr/local/include/kernel_headers_%{KERNELVERSION}/usr/include/" \
        LDFLAGS="-flinker-output=nolto-rel" \
        --program-prefix=%{?_program_prefix} \
        --disable-dependency-tracking \
        --prefix=%{_prefix} \
        --exec-prefix=%{_prefix} \
        --bindir=%{_bindir} \
        --sbindir=%{_sbindir} \
        --sysconfdir=%{_sysconfdir} \
        --datadir=%{_datadir} \
        --includedir=%{_includedir} \
        --libdir=%{_libdir} \
        --libexecdir=%{_libexecdir} \
        --localstatedir=%{_localstatedir} \
        --sharedstatedir=%{_sharedstatedir} \
        --mandir=%{_mandir} \
        --infodir=%{_infodir} \
        --disable-profile \
        --disable-werror \
        --enable-kernel=%{KERNELVERSION} \
        --enable-bind-now \
        --enable-cet \
        --enable-stack-protector=strong \
        --disable-experimental-malloc \
        --disable-silent-rules \
        libc_cv_slibdir=%{_libdir}

# Sometimes we have false "out of memory" make error
# just rerun/continue make to workaroung it.
%make_build || %make_build || %make_build

%install
#       Do not remove static libs
pushd %{_builddir}/glibc-build
#       Create directories
make install_root=%{buildroot} install %{?_smp_mflags}
install -vdm 755 %{buildroot}%{_sysconfdir}/ld.so.conf.d
install -vdm 755 %{buildroot}%{_sharedstatedir}/cache/nscd
install -vdm 755 %{buildroot}%{_libdir}/locale
cp -v ../%{name}-%{version}/nscd/nscd.conf %{buildroot}%{_sysconfdir}/nscd.conf
#       Install locale generation script and config file
cp -v %{SOURCE2} %{buildroot}%{_sysconfdir}
cp -v %{SOURCE1} %{buildroot}%{_sbindir}
#       Remove unwanted cruft
rm -rf %{buildroot}%{_infodir}
#       Install configuration files

# Spaces should not be used in nsswitch.conf in the begining of new line
# Only tab should be used as it expects the same in source code.
# Otherwise "altfiles" will not be added. which may cause dbus.service failure
cat > %{buildroot}%{_sysconfdir}/nsswitch.conf <<- "EOF"
#       Begin /etc/nsswitch.conf

passwd: files
group: files
shadow: files

hosts: files dns
networks: files

protocols: files
services: files
ethers: files
rpc: files
#       End /etc/nsswitch.conf
EOF
cat > %{buildroot}%{_sysconfdir}/ld.so.conf <<- "EOF"
#       Begin /etc/ld.so.conf
    /usr/local/lib
    /opt/lib
    include %{_sysconfdir}/ld.so.conf.d/*.conf
EOF
# Create empty ld.so.cache
:> %{buildroot}%{_sysconfdir}/ld.so.cache
popd

%find_lang %{name} --all-name
pushd localedata
# Generate out of locale-archive an (en_US.) UTF-8 locale
mkdir -p %{buildroot}%{_libdir}/locale
if [ %{_host} != %{_build} ]; then
  LOCALEDEF=localedef
else
  LOCALEDEF=../../glibc-build/locale/localedef
fi

I18NPATH=. GCONV_PATH=../../glibc-build/iconvdata LC_ALL=C ../../glibc-build/elf/ld.so --library-path ../../glibc-build $LOCALEDEF --no-archive --prefix=%{buildroot} -A ../intl/locale.alias -i locales/en_US -c -f charmaps/UTF-8 en_US.UTF-8

mv %{buildroot}%{_libdir}/locale/en_US.utf8 %{buildroot}%{_libdir}/locale/en_US.UTF-8

popd

mv %{buildroot}/sbin/* %{buildroot}/%{_sbindir}
rmdir %{buildroot}/sbin

%if 0%{?with_check}
%check
cd %{_builddir}/glibc-build
make %{?_smp_mflags} check ||:
# These 2 persistant false positives are OK
# XPASS for: elf/tst-protected1a and elf/tst-protected1b
[ $(grep ^XPASS tests.sum | wc -l) -ne 2 -a $(grep "^XPASS: elf/tst-protected1[ab]" tests.sum | wc -l) -ne 2 ] && exit 1 ||:

# FAIL (intermittent) in chroot but PASS in container:
# posix/tst-spawn3 and stdio-common/test-vfprintf
n=0

grep "^FAIL: c++-types-check" tests.sum >/dev/null && n=$((n+1)) ||:
# can fail in chroot
grep "^FAIL: io/tst-fchownat" tests.sum >/dev/null && n=$((n+1)) ||:
grep "^FAIL: malloc/tst-tcfree2" tests.sum >/dev/null && n=$((n+1)) ||:
# can timeout
grep "^FAIL: nptl/tst-mutex10" tests.sum >/dev/null && n=$((n+1)) ||:
# can fail in chroot
grep "^FAIL: nptl/tst-setuid3" tests.sum >/dev/null && n=$((n+1)) ||:
grep "^FAIL: stdlib/tst-secure-getenv" tests.sum >/dev/null && n=$((n+1)) ||:
grep "^FAIL: support/tst-support_descriptors" tests.sum >/dev/null && n=$((n+1)) ||:
#https://sourceware.org/glibc/wiki/Testing/Testsuite
grep "^FAIL: nptl/tst-eintr1" tests.sum >/dev/null && n=$((n+1)) ||:
#This happens because the kernel fails to reap exiting threads fast enough,
#eventually resulting an EAGAIN when pthread_create is called within the test.

# check for exact 'n' failures
[ $(grep ^FAIL tests.sum | wc -l) -ne $n ] && exit 1 ||:
%endif

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%posttrans iconv
%{_sbindir}/iconvconfig

%postun iconv
if [ -e %{_lib64dir}/gconv/gconv-modules.cache ]; then
  rm %{_lib64dir}/gconv/gconv-modules.cache
fi

%files
%defattr(-,root,root)
%{_libdir}/locale/*
%dir %{_sysconfdir}/ld.so.conf.d
%config(noreplace) %{_sysconfdir}/nsswitch.conf
%config(noreplace) %{_sysconfdir}/ld.so.conf
%config(noreplace) %{_sysconfdir}/rpc
%attr(0644,root,root) %config(missingok,noreplace) %{_sysconfdir}/ld.so.cache
%config %{_sysconfdir}/locale-gen.conf
%{_sbindir}/ldconfig
%{_sbindir}/locale-gen.sh
%{_bindir}/*
%{_libexecdir}/*
%{_datadir}/i18n/charmaps/UTF-8.gz
%{_datadir}/i18n/charmaps/ISO-8859-1.gz
%{_datadir}/i18n/locales/en_US
%{_datadir}/i18n/locales/en_GB
%{_datadir}/i18n/locales/i18n*
%{_datadir}/i18n/locales/iso14651_t1
%{_datadir}/i18n/locales/iso14651_t1_common
%{_datadir}/i18n/locales/translit_*
%{_datadir}/locale/locale.alias
%exclude %{_sharedstatedir}/nss_db/Makefile
%exclude %{_bindir}/iconv
%exclude %{_bindir}/mtrace
%exclude %{_bindir}/pcprofiledump
%exclude %{_bindir}/pldd
%exclude %{_bindir}/sotruss
%exclude %{_bindir}/sprof
%exclude %{_bindir}/xtrace

%files libs
%defattr(-,root,root)
%{_libdir}/*.so
%{_libdir}/*.so.*
%exclude %{_libdir}/libpcprofile.so

%files iconv
%defattr(-,root,root)
%{_libdir}/gconv/*
%{_bindir}/iconv
%{_sbindir}/iconvconfig

%files tools
%defattr(-,root,root)
%{_bindir}/mtrace
%{_bindir}/pcprofiledump
%{_bindir}/pldd
%{_bindir}/sotruss
%{_bindir}/sprof
%{_bindir}/xtrace
%{_bindir}/zdump
%{_sbindir}/zic
%{_sbindir}/sln
%{_libdir}/audit/*
%{_libdir}/libpcprofile.so

%files nscd
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/nscd.conf
%{_sbindir}/nscd
%dir %{_sharedstatedir}/cache/nscd

%files i18n
%defattr(-,root,root)
%{_datadir}/i18n/charmaps/*.gz
%{_datadir}/i18n/locales/*
%exclude %{_datadir}/i18n/charmaps/UTF-8.gz
%exclude %{_datadir}/i18n/charmaps/ISO-8859-1.gz
%exclude %{_datadir}/i18n/locales/en_US
%exclude %{_datadir}/i18n/locales/en_GB
%exclude %{_datadir}/i18n/locales/i18n*
%exclude %{_datadir}/i18n/locales/iso14651_t1
%exclude %{_datadir}/i18n/locales/iso14651_t1_common
%exclude %{_datadir}/i18n/locales/translit_*

%files devel
%defattr(-,root,root)
%{_libdir}/*.a
%{_libdir}/*.o
%{_includedir}/*

%files -f %{name}.lang lang
%defattr(-,root,root)
