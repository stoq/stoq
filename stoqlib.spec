%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A powerful retail system library
Name: stoqlib
Version: 0.9.1
Release: 1
License: LGPL
Group: System Environment/Libraries
URL: http://www.stoq.com.br/
Source: http://download.stoq.com.br/sources/0.8.9/stoqlib-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: pygtk2 >= 2.8.1, python-zope-interface >= 3.0.1, stoqdrivers >= 0.8.0, python-kiwi >= 1.9.16, python-psycopg2 >= 2.0.5, gazpacho >= 0.6.6, python-imaging >= 1.1.5, python-reportlab >= 1.20
Requires: python-abi = %(%{__python} -c "import sys; print sys.version[:3]")
BuildRequires: python-kiwi >= 1.9.15, python-reportlab >= 1.20, python-psycopg2 >= 2.0.5
BuildArch: noarch

%description
Stoqlib offers many special tools for retail system applications
such reports infrastructure, basic dialogs and searchbars and
domain data in a persistent level.

%prep
%setup -q -n stoqlib-%{version}
sed -i -e 's|share/doc/stoqlib|share/doc/%{name}-%{version}|' setup.py

%setup

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
rm -rf %{buildroot}%{_defaultdocdir}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS CONTRIBUTORS COPYING README
%{python_sitelib}/stoqlib
%{_libdir}/stoqlib
%{_datadir}/locale/*/LC_MESSAGES/stoqlib.mo
%{_datadir}/stoqlib/fonts
%{_datadir}/stoqlib/glade
%{_datadir}/stoqlib/pixmaps
%{_datadir}/stoqlib/sql
%{_datadir}/stoqlib/csv
%{_datadir}/stoqlib/template

%changelog
* Mon Jul 16 2007 Johan Dahlin <jdahlin@async.com.br> 0.9.1-1
- New release

* Tue Feb 03 2007 Johan Dahlin <jdahlin@async.com.br> 0.8.10-1
- New release

* Tue Feb 03 2007 Johan Dahlin <jdahlin@async.com.br> 0.8.9-1
- Initial RPM release.

