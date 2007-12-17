# Copyright (c) 2000-2005, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

%define _with_gcj_support 1
%define gcj_support %{?_with_gcj_support:1}%{!?_with_gcj_support:%{?_without_gcj_support:0}%{!?_without_gcj_support:%{?_gcj_support:%{_gcj_support}}%{!?_gcj_support:0}}}


%define repo_dir    .m2/repository

%define namedversion 1.0-alpha-8
%define maven_settings_file %{_builddir}/%{name}-%{namedversion}/settings.xml

Name:           modello
Version:        1.0
Release:        %mkrel 0.1.a8.4.3.4
Epoch:          0
Summary:        Modello Data Model toolkit
License:        MIT  
Group:          Development/Java
URL:            http://modello.codehaus.org/
Source0:        %{name}-%{namedversion}-src.tar.gz
# svn export svn://svn.modello.codehaus.org/modello/tags/modello-1.0-alpha-8/
# tar czf modello-1.0-alpha-8-src.tar.gz modello-1.0-alpha-8/
Source1:        modello.script

Source2:                %{name}-jpp-depmap.xml

Patch0:                 modello-hibernateold-artifactid-fix.patch
Patch1:                 modello-build-all-plugins.patch
%if %{gcj_support}
BuildRequires:          java-gcj-compat-devel
%endif
%if ! %{gcj_support}
BuildArch:      noarch
%endif

BuildRequires:  ant >= 0:1.6
BuildRequires:  java-rpmbuild >= 0:1.7.2
BuildRequires:  maven2 >= 2.0.4-9
BuildRequires:  maven2-plugin-compiler
BuildRequires:  maven2-plugin-install
BuildRequires:  maven2-plugin-jar
BuildRequires:  maven2-plugin-javadoc
BuildRequires:  maven2-plugin-release
BuildRequires:  maven2-plugin-resources
BuildRequires:  maven2-plugin-surefire
BuildRequires:  maven2-plugin-plugin
BuildRequires:  classworlds >= 0:1.1
BuildRequires:  dtdparser
BuildRequires:  plexus-container-default
BuildRequires:  plexus-utils
BuildRequires:  plexus-velocity
BuildRequires:  velocity

Requires:       classworlds >= 0:1.1
Requires:       dtdparser
Requires:       plexus-container-default
Requires:       plexus-utils
Requires:       plexus-velocity
Requires:       velocity

Requires(post):    jpackage-utils >= 0:1.7.2
Requires(postun):  jpackage-utils >= 0:1.7.2

Provides:       modello-maven-plugin = %{epoch}:%{version}-%{release}
Obsoletes:      modello-maven-plugin < 0:1.0-0.a8.3jpp

%description
Modello is a Data Model toolkit in use by the 
http://maven.apache.org/maven2.
It all starts with the Data Model. Once a data model is defined, 
the toolkit can be used to generate any of the following at compile 
time.
Java POJOs of the model.
Java POJOs to XML Writer (provided via xpp3 or dom4j).
XML to Java Pojos Reader (provided via xpp3 or dom4j).
XDoc documentation of the data model.
Java model to [Prevayler|http://www.prevayler.org/] Store.
Java model to [JPOX|http://www.jpox.org/] Store.
Java model to [JPOX|http://www.jpox.org/] Mapping.


%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java
Requires(post):   /bin/rm,/bin/ln
Requires(postun): /bin/rm

%description javadoc
Javadoc for %{name}.

%prep
%setup -q -n %{name}-%{namedversion}
%patch0 -b .sav
%patch1 -b .sav

find . -name release-pom.xml -exec rm -f '{}' \;

for i in modello-plugins-sandbox/modello-plugin-ldap/src/test/java/org/codehaus/modello/plugin/ldap/ObjStateFactoryModelloGeneratorTest.java \
         modello-plugins-sandbox/modello-plugin-ldap/src/test/java/org/codehaus/modello/plugin/ldap/LdapSchemaGeneratorTest.java \
         modello-plugins-sandbox/modello-plugin-ojb/src/test/java/org/codehaus/modello/plugin/ojb/OjbModelloGeneratorTest.java \
         modello-plugins-sandbox/modello-plugin-stash/src/test/java/org/codehaus/modello/plugin/stash/StashModelloGeneratorTest.java \
         modello-plugins-sandbox/modello-plugin-hibernate-store/src/test/java/org/codehaus/modello/plugin/hibernate/HibernateModelloGeneratorTest.java; do
        sed -i -e s:org.codehaus.modello.ModelloGeneratorTest:org.codehaus.modello.AbstractModelloGeneratorTest:g $i
        sed -i -e s:"extends ModelloGeneratorTest":"extends AbstractModelloGeneratorTest":g $i
done

%build

export MAVEN_REPO_LOCAL=$(pwd)/.m2/repository
mkdir -p $MAVEN_REPO_LOCAL

mvn-jpp \
        -e \
                -Dmaven.repo.local=$MAVEN_REPO_LOCAL \
                -Dmaven2.jpp.depmap.file=%{SOURCE2} \
        -Dmaven.test.failure.ignore=true \
        install javadoc:javadoc

%install
rm -rf $RPM_BUILD_ROOT

# poms
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/maven2/poms
for i in `find . -name pom.xml | grep -v \\\./pom.xml`; do
        cp -p $i $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP.`basename \`dirname $i\``.pom
done

# Depmap fragments
for i in `find . -name pom.xml | grep -v \\\./pom.xml |  grep -v modello-plugins-sandbox`; do
    # i is in format ..../artifactid/pom.xml
    artifactname=`basename \`dirname $i\` | sed -e s:^modello-::g`

    %add_to_maven_depmap org.codehaus.modello modello-$artifactname %{namedversion} JPP/%{name} $artifactname
done

# sandbox plugins are a different version
for i in `find . -name pom.xml | grep modello-plugins-sandbox`; do
        # i is in format ..../artifactid/pom.xml
        artifactname=`basename \`dirname $i\` | sed -e s:^modello-::g`

        %add_to_maven_depmap org.codehaus.modello modello-$artifactname 1.0-alpha-4-SNAPSHOT JPP/%{name} $artifactname
done

cp -p pom.xml $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP.modello-modello.pom
%add_to_maven_depmap org.codehaus.modello modello %{namedversion} JPP/%{name} modello

# script
install -d -m 755 $RPM_BUILD_ROOT%{_bindir}
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_bindir}/%{name}

# jars
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}/%{name}
for jar in $(find -type f -name "*.jar" | grep -E target/.*.jar); do 
        install -m 644 $jar $RPM_BUILD_ROOT%{_javadir}/%{name}/`basename $jar |sed -e s:modello-::g`
done

(cd $RPM_BUILD_ROOT%{_javadir}/%{name} && for jar in *-%{namedversion}*; do ln -sf ${jar} `echo $jar| sed  "s|-%{namedversion}||g"`; done)

# Do it again for sandbox plugins, which have a different version
(cd $RPM_BUILD_ROOT%{_javadir}/%{name} && for jar in *-1.0-alpha-4-SNAPSHOT*; do ln -sf ${jar} `echo $jar| sed  "s|-1.0-alpha-4-SNAPSHOT||g"`; done)

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
for target in $(find -type d -name target); do
  install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}/`basename \`dirname $target\` | sed -e s:modello-::g`
  cp -pr $target/site/apidocs/* $jar $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}/`basename \`dirname $target\` | sed -e s:modello-::g`
done
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
%if %{gcj_support}
%{update_gcjdb}
%endif
%update_maven_depmap

%postun
%if %{gcj_support}
%{clean_gcjdb}
%endif
%update_maven_depmap


%files
%defattr(-,root,root,-)
%{_datadir}/maven2
%dir %{_javadir}/%{name}
%{_javadir}/%{name}
%attr(755,root,root) %{_bindir}/*
%{_mavendepmapfragdir}
%if %{gcj_support}
%attr(-,root,root) %dir %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/*.jar.*
%endif
%config(noreplace) /etc/maven/fragments/modello


%files javadoc
%defattr(-,root,root,-)
%doc %{_javadocdir}/*
