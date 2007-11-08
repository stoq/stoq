# $Id$
# Authority: jdahlin

%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Fiscal driver collection
Name: stoqdrivers
Version: 0.9.1
Release: 1
License: LGPL
Group: System Environment/Libraries
URL: http://www.stoq.com.br/
Source: http://download.stoq.com.br/sources/0.8.9/stoqdrivers-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: pygobject2 >= 2.8.0, python-zope-interface >= 3.0.1, pyserial >= 2.2, python-kiwi >= 1.9.19
Requires: python-abi = %(%{__python} -c "import sys; print sys.version[:3]")
BuildRequires: python-kiwi >= 1.9.19
BuildArch: noarch

%description
This is a powerful collection of device drivers written in Python and totally
focused on retail systems. Stoqdrivers also offers an unified API for devices
like fiscal printers which makes it easy to embed in many applications.

%prep

%setup

%build

%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install --root=%{buildroot}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS ChangeLog COPYING NEWS README
%{python_sitelib}/stoqdrivers
%{_datadir}/locale/*/LC_MESSAGES/stoqdrivers.mo
%{_datadir}/stoqdrivers/conf/*.ini

%changelog
* Thu Nov 08 2007 Fabio Morbec <fabio@async.com.br> 0.9.1
- New Release.

* Thu Aug 30 2007 Fabio Morbec <fabio@async.com.br> 0.9.0
- Initial RPM release.

