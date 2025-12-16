#
# spec file for package python-aws-mp-utils
#
# Copyright (c) 2025 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

%define upstream_name aws-mp-utils
%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif
%global _sitelibdir %{%{pythons}_sitelib}

Name:           python-aws-mp-utils
Version:        0.1.0
Release:        0
Summary:        Functions and CLI for AWS Marketplace-Catalog APIs
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/aws-mp-utils
Source:         https://files.pythonhosted.org/packages/source/a/aws-mp-utils/aws-mp-utils-%{version}.tar.gz
BuildRequires:  fdupes
BuildRequires:  %{pythons}-pip
BuildRequires:  %{pythons}-wheel
BuildRequires:  %{pythons}-pytest
BuildRequires:  %{pythons}-jmespath
BuildRequires:  %{pythons}-click
BuildRequires:  %{pythons}-PyYAML
BuildRequires:  %{pythons}-boto3
Requires:       %{pythons}-jmespath
Requires:       %{pythons}-click
Requires:       %{pythons}-PyYAML
Requires:       %{pythons}-boto3
BuildArch:      noarch

%description
Utility functions and CLI for working with AWS Marketplace-Catalog APIs

%prep
%autosetup -n aws-mp-utils-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%fdupes %{buildroot}%{_sitelibdir}

%check
%pytest

%files
%license LICENSE
%doc CHANGES.md README.md
%{_sitelibdir}/aws_mp_utils/
%{_sitelibdir}/aws_mp_utils-*.dist-info/
%{_bindir}/aws-mp-utils

%changelog
