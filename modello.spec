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

Name:           modello
Version:        1.4.1
Release:        4
Summary:        Modello Data Model toolkit
License:        MIT
Group:          Development/Java
URL:            http://modello.codehaus.org/
Source0:        http://repo2.maven.org/maven2/org/codehaus/%{name}/%{name}/%{version}/%{name}-%{version}-source-release.zip

Source2:        %{name}-jpp-depmap.xml

Patch0:         0001-Use-public-function-for-component-lookup.patch

BuildArch:      noarch

BuildRequires:  ant >= 0:1.6
BuildRequires:  jpackage-utils >= 0:1.7.2
BuildRequires:  maven2 >= 2.0.4-9
BuildRequires:  maven-assembly-plugin
BuildRequires:  maven-compiler-plugin
BuildRequires:  maven-install-plugin
BuildRequires:  maven-jar-plugin
BuildRequires:  maven-javadoc-plugin
BuildRequires:  maven-resources-plugin
BuildRequires:  maven-surefire-plugin
BuildRequires:  maven-site-plugin
BuildRequires:  maven-surefire-provider-junit
BuildRequires:  maven-dependency-plugin
BuildRequires:  maven-plugin-plugin
BuildRequires:  maven-shared-reporting-impl
BuildRequires:  maven-shared-invoker
BuildRequires:  classworlds >= 0:1.1
BuildRequires:  plexus-container-default
BuildRequires:  plexus-utils
BuildRequires:  plexus-velocity
BuildRequires:  velocity
BuildRequires:  maven-doxia
BuildRequires:  maven-doxia-sitetools
BuildRequires:  maven-doxia-tools
BuildRequires:  plexus-build-api
BuildRequires:  ws-jaxme
BuildRequires:  xmlunit
BuildRequires:  jpa_api = 3.0
BuildRequires:  geronimo-parent-poms

Requires:       classworlds >= 0:1.1
Requires:       plexus-containers-container-default
Requires:       plexus-build-api
Requires:       plexus-utils
Requires:       plexus-velocity
Requires:       velocity
Requires:       guava
Requires:       xbean

Requires:          jpackage-utils
Requires(post):    jpackage-utils
Requires(postun):  jpackage-utils

Provides:       modello-maven-plugin = %{version}-%{release}
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
Requires:       jpackage-utils

%description javadoc
API documentation for %{name}.

%prep
%setup -q -n %{name}-%{version}

# fix test compilation failure with new plexus-containers
# not really needed now because we are skipping tests for other
# problems...
#%%patch0 -p1


%build

export MAVEN_REPO_LOCAL=$(pwd)/.m2/repository
mkdir -p $MAVEN_REPO_LOCAL

# skip tests because we have too old xmlunit in Fedora now (1.0.8)
mvn-jpp \
        -e \
        -Dmaven.repo.local=$MAVEN_REPO_LOCAL \
        -Dmaven2.jpp.depmap.file=%{SOURCE2} \
        -Dmaven.test.skip=true \
        install javadoc:aggregate

%install
# poms and depmap fragments
install -d -m 755 $RPM_BUILD_ROOT%{_mavenpomdir}
for i in `find . -name pom.xml -not -path ./pom.xml -not -path "*src/it/*"`; do
    # i is in format ..../artifactid/pom.xml
    cp -p $i $RPM_BUILD_ROOT%{_mavenpomdir}/JPP.`basename \`dirname $i\``.pom

    artifactname=`basename \`dirname $i\` | sed -e s:^modello-::g`
    %add_to_maven_depmap org.codehaus.modello modello-$artifactname %{version} JPP/%{name} $artifactname
done

cp -p pom.xml $RPM_BUILD_ROOT%{_mavenpomdir}/JPP.modello-modello.pom
%add_to_maven_depmap org.codehaus.modello modello %{version} JPP/%{name} modello

# script
install -d -m 755 $RPM_BUILD_ROOT%{_bindir}
%jpackage_script org.codehaus.modello.ModelloCli "" ""  "modello/core:modello/plugin-xpp3:modello/plugin-xml:guava:xbean:plexus/containers-container-default:plexus/utils:plexus/classworlds)" %{name} true

# jars

install -d -m 755 $RPM_BUILD_ROOT%{_javadir}/%{name}
for jar in $(find -type f -name "*-%{version}.jar" | grep -E target/.*.jar); do
        install -m 644 $jar $RPM_BUILD_ROOT%{_javadir}/%{name}/`basename $jar |sed -e s:modello-::g|sed -e s:-%{version}::g`
done

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
cp -pr target/site/apidocs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
(cd $RPM_BUILD_ROOT%{_javadocdir} && ln -sf %{name}-%{version} %{name})

%post
%update_maven_depmap

%postun
%update_maven_depmap

%files
%defattr(-,root,root,-)
%{_mavenpomdir}/*
%{_javadir}/%{name}
%{_bindir}/*
%config(noreplace) %{_mavendepmapfragdir}/*

%files javadoc
%defattr(-,root,root,-)
%{_javadocdir}/%{name}-%{version}
%{_javadocdir}/%{name}

