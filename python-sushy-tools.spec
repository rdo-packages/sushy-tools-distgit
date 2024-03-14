%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2ef3fe0ec2b075ab7458b5f8b702b20b13df2318
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
# we are excluding some BRs from automatic generator
%global excluded_brs doc8 bandit pre-commit hacking flake8-import-order

%global with_doc 1
%global sname sushy-tools
%global fname sushy_tools
%global common_desc A set of tools to support the development and test of the Sushy library
%global common_desc_tests Tests for sushy-tools library

Name: python-%{sname}
Version: 1.1.0
Release: 1%{?dist}
Summary: %{common_desc}
License: Apache-2.0
URL: https://opendev.org/openstack/sushy-tools

Source0: https://tarballs.opendev.org/openstack/%{sname}/%{sname}-%{upstream_version}.tar.gz
Source1: sushy-emulator.service
Source2: sushy-emulator.conf
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101: http://tarballs.openstack.org/%{sname}/%{sname}-%{upstream_version}.tar.gz.asc
Source102: https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif

BuildRequires: git-core
BuildArch: noarch

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
BuildRequires:  /usr/bin/gpgv2
BuildRequires:  openstack-macros
%endif

%description
%{common_desc}

%package -n python3-%{sname}
Summary: %{common_desc}

BuildRequires: python3-devel
BuildRequires: pyproject-rpm-macros
%description -n python3-%{sname}
%{common_desc}

%package -n python3-%{sname}-tests
Summary: sushy-tools tests
Requires: python3-%{sname} = %{version}-%{release}

Requires: python3-libvirt
Requires: python3-munch
Requires: python3-openstacksdk
Requires: python3-oslotest
Requires: python3-testscenarios
Requires: python3-testtools

%description -n python3-%{sname}-tests
%{common_desc_tests}

%if 0%{?with_doc}
%package -n python-%{sname}-doc
Summary: sushy-tools documentation

%description -n python-%{sname}-doc
Documentation for sushy-tools
%endif

%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%autosetup -n %{sname}-%{upstream_version} -S git


sed -i /^[[:space:]]*-c{env:.*_CONSTRAINTS_FILE.*/d tox.ini
sed -i "s/^deps = -c{env:.*_CONSTRAINTS_FILE.*/deps =/" tox.ini
sed -i /^minversion.*/d tox.ini
sed -i /^requires.*virtualenv.*/d tox.ini

# Exclude some bad-known BRs
for pkg in %{excluded_brs};do
  for reqfile in doc/requirements.txt test-requirements.txt; do
    if [ -f $reqfile ]; then
      sed -i /^${pkg}.*/d $reqfile
    fi
  done
done

# Automatic BR generation
%generate_buildrequires
%if 0%{?with_doc}
  %pyproject_buildrequires -t -e %{default_toxenv},docs
%else
  %pyproject_buildrequires -t -e %{default_toxenv}
%endif

%build
%pyproject_wheel

%if 0%{?with_doc}
# generate html docs
%tox -e docs
# remove the sphinx-build-3 leftovers
rm -rf doc/build/html/.{doctrees,buildinfo}
%endif

%install
%pyproject_install
# Install systemd script
mkdir -p %{buildroot}%{_unitdir}
install -p -D -m 644 %{SOURCE1} %{buildroot}/%{_unitdir}/sushy-emulator.service
# Install distribution config
mkdir -p %{buildroot}%{_sysconfdir}/sushy-emulator/
install -p -D -m 640 %{SOURCE2} %{buildroot}/%{_sysconfdir}/sushy-emulator/sushy-emulator.conf

%check
%tox -e %{default_toxenv}

%pre -n python3-%{sname}
getent group sushy-tools >/dev/null || groupadd -r sushy-tools
getent passwd sushy-tools >/dev/null || useradd -r \
    -g sushy-tools -M -s /sbin/nologin -c "Redfish Emulator" sushy-tools

%preun -n python3-%{sname}
%systemd_preun sushy-emulator.service

%post -n python3-%{sname}
%systemd_post sushy-emulator.service

%postun -n python3-%{sname}
%systemd_postun_with_restart sushy-emulator.service

%files -n python3-%{sname}
%license LICENSE
%{_bindir}/sushy-emulator
%{_bindir}/sushy-static
%{python3_sitelib}/%{fname}
%{python3_sitelib}/%{fname}-*.dist-info
%{_unitdir}/sushy-emulator.service
%dir %attr(-, root, sushy-tools) %{_sysconfdir}/sushy-emulator
%config(noreplace) %attr(-, root, sushy-tools) %{_sysconfdir}/sushy-emulator/sushy-emulator.conf
%exclude %{python3_sitelib}/%{dname}/tests

%files -n python3-%{sname}-tests
%license LICENSE
%{python3_sitelib}/%{fname}/tests

%if 0%{?with_doc}
%files -n python-%{sname}-doc
%license LICENSE
%doc doc/build/html README.rst
%endif

%changelog
* Thu Mar 14 2024 RDO <dev@lists.rdoproject.org> 1.1.0-1
- Update to 1.1.0

