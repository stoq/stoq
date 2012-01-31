%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A powerful retail system
Name: stoq
Version: 1.2
Release: 1
License: GPL
Group: System Environment/Libraries
URL: http://www.stoq.com.br/
Source: http://download.stoq.com.br/sources/1.0/stoq-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: postgresql >= 8.4
Requires: pygtk2 >= 2.17
Requires: pypoppler >= 0.12.1
Requires: python-abi = %(%{__python} -c "import sys; print sys.version[:3]")
Requires: python-dateutil >= 1.4.1
Requires: python-imaging >= 1.1.5
Requires: python-gudev >= 147
Requires: python-kiwi >= 1.9.30
Requires: python-mako >= 0.2.5
Requires: python-psycopg2 >= 2.0.5
Requires: python-reportlab >= 2.4
Requires: python-zope-interface >= 3.0.1
Requires: stoqdrivers >= 0.9.14
Requires: pywebkitgtk >= 1.1.7
Requires: python-twisted-core >= 10.0.0
Requires: python-twisted-web >= 10.0.0
BuildRequires: python-kiwi >= 1.9.28
BuildArch: noarch

%description
Stoq is a suite of Retail Management System applications.
It includes the following applications;
Point of Sales, Cash register, Sales, Purchase Orders, Inventory control,
Customer Relationship Management (CRM), Financial Accounting, Accounts Payable and
Accounts Receivable, Printable Reports, Employees and Suppliers registry.

%prep
%setup -q -n stoq-%{version}

%build
%{__python} setup.py build

%install
sed -i -e 's|share/doc/stoqlib|share/doc/%{name}-%{version}|' setup.py
sed -i -e 's|share/doc/stoq|share/doc/%{name}-%{version}|' setup.py
mkdir -p %{_etcdir}/stoq
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
rm -rf %{buildroot}%{_defaultdocdir}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS CONTRIBUTORS COPYING COPYING.pt_BR README NEWS
%{_bindir}/stoq
%{_bindir}/stoqcreatedbuser
%{_bindir}/stoqdbadmin
%{_bindir}/stoq-daemon
%{_libdir}/python*/site-packages/*.egg-info
%{_sysconfdir}/stoq
%{_datadir}/icons/hicolor/48x48/apps/stoq.png
%{_datadir}/polkit-1/actions/br.com.stoq.createdatabase.policy
%{_datadir}/stoq/csv
%{_datadir}/stoq/fonts
%{_datadir}/stoq/glade
%{_datadir}/stoq/html
%{_datadir}/stoq/misc
%{_datadir}/stoq/pixmaps
%{_datadir}/stoq/sql
%{_datadir}/stoq/template
%{_datadir}/stoq/uixml
%{_datadir}/locale/*/LC_MESSAGES/stoq.mo
%{_datadir}/applications/stoq.desktop
%{_datadir}/gnome/help
%{python_sitelib}/stoq
%{python_sitelib}/stoqlib

%changelog
* Tue Nov 08 2011 Ronaldo Maia <romaia@async.com.br> 1.0.5-1
- Bugfixes release

* Mon Oct 24 2011 Ronaldo Maia <romaia@async.com.br> 1.0.4-1
- Bugfixes release

* Tue Oct 18 2011 Ronaldo Maia <romaia@async.com.br> 1.0.3-1
- Fix a bug in configuration wizard

* Tue Aug 16 2011 Ronaldo Maia <romaia@async.com.br> 1.0.2.1-1
- Fix a bug in configuration wizard

* Fri Aug 12 2011 Ronaldo Maia <romaia@async.com.br> 1.0.2-1
- Bugfixes release

* Thu Aug 08 2011 Ronaldo Maia <romaia@async.com.br> 1.0.1-1
- Bugfixes release

* Thu Jul 28 2011 Ronaldo Maia <romaia@async.com.br> 1.0.0-3
- Bugfixes

* Thu Jul 14 2011 Johan Dahlin <jdahlin@async.com.br> 1.0.0-2
- Bump Stoqdrivers and kiwi dependencies

* Thu Jul 14 2011 Johan Dahlin <jdahlin@async.com.br> 1.0.0-1
- Release 1.0

* Wed Feb 11 2008 Fabio Morbec <fabio@async.com.br> 0.9.4-4
- Fix

* Wed Jan 31 2008 Fabio Morbec <fabio@async.com.br> 0.9.4-3
- Fix

* Wed Jan 31 2008 Fabio Morbec <fabio@async.com.br> 0.9.4-1
- New version.

* Wed Nov 07 2007 Fabio Morbec <fabio@async.com.br> 0.9.3-4
- New version.

* Wed Nov 07 2007 Fabio Morbec <fabio@async.com.br> 0.9.3-1
- New version.

* Thu Jul 30 2007 Fabio Morbec <fabio@async.com.br> 0.9.2-1
- New version.

* Mon Jul 16 2007 Johan Dahlin <jdahlin@async.com.br> 0.9.1-1
- New version.

* Tue Mar 26 2007 Johan Dahlin <jdahlin@async.com.br> 0.8.10-1
- New version.

* Tue Feb 03 2007 Johan Dahlin <jdahlin@async.com.br> 0.8.9-1
- Initial RPM release.
