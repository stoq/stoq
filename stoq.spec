%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A powerful retail system
Name: stoq
Version: 0.8.9
Release: 1
License: GPL
Group: System Environment/Libraries
URL: http://www.stoq.com.br/
Source: http://download.stoq.com.br/sources/0.8.9/stoq-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: python-kiwi >= 1.9.13, stoqlib >= 0.8.9
Requires: python-abi = %(%{__python} -c "import sys; print sys.version[:3]")
BuildRequires: python-kiwi >= 1.9.13, stoqlib >= 0.8.9
BuildArch: noarch

%description
Stoq is an advanced retails system which has as main goals the
usability, good devices support, and useful features for retails.

%prep
%setup -q -n stoq-%{version}

%build
%{__python} setup.py build

%install
sed -i -e 's|share/doc/stoq|share/doc/%{name}-%{version}|' setup.py
mkdir -p %{_etcdir}/stoq
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
rm -rf %{buildroot}%{_defaultdocdir}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS CONTRIBUTORS COPYING README NEWS
%{_bindir}/stoq
%{_bindir}/stoqdbadmin
%{_sysconfdir}/stoq
%{_datadir}/locale/*/LC_MESSAGES/stoq.mo
%{_datadir}/stoq/glade
%{_datadir}/stoq/pixmaps
%{_datadir}/applications/stoq.desktop
%{python_sitelib}/stoq

%changelog
* Tue Feb 03 2007 Johan Dahlin <jdahlin@async.com.br> 0.8.9-1
- Initial RPM release.

