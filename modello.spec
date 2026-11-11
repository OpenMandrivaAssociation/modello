Name:		modello
Version:	2.1.2
Release:	1
Summary:	Code generator for Maven model sources
Group:		Development/Java
License:	MIT
URL:		https://github.com/codehaus-plexus/modello
# Tag modello-2.1.2. Maven 3.9.5 generates its model sources with
# the java, xpp3-reader, xpp3-writer, xpp3-extended-reader, and
# xpp3-extended-writer goals from this release.
Source0:	https://github.com/codehaus-plexus/modello/archive/refs/tags/modello-%{version}.tar.gz#/%{name}-%{version}.tar.gz
# Sisu 0.3.5 leaves classpath scanning off, so the CLI never sees
# @Component classes. The other hunk uses the BuildContext cooker
# already publishes (org.sonatype.plexus:plexus-build-api 0.0.7).
Patch0:		modello-sisu-index.patch

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	python
BuildRequires:	mvn(org.codehaus.plexus:plexus-utils)
BuildRequires:	mvn(org.codehaus.plexus:plexus-xml) = 4.0.0
BuildRequires:	mvn(org.sonatype.plexus:plexus-build-api) = 0.0.7
BuildRequires:	mvn(org.eclipse.sisu:org.eclipse.sisu.inject) = 0.3.5
BuildRequires:	mvn(org.eclipse.sisu:org.eclipse.sisu.plexus) = 0.3.5
BuildRequires:	mvn(com.google.inject:guice)
BuildRequires:	mvn(com.google.guava:guava)
BuildRequires:	mvn(com.google.guava:failureaccess) = 1.0.3
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	mvn(aopalliance:aopalliance)
BuildRequires:	mvn(org.codehaus.plexus:plexus-classworlds) = 2.9.0
BuildRequires:	mvn(org.codehaus.plexus:plexus-component-annotations)
BuildRequires:	mvn(org.slf4j:slf4j-api)
Requires:	mvn(org.codehaus.plexus:plexus-xml) = 4.0.0
Requires:	mvn(org.sonatype.plexus:plexus-build-api) = 0.0.7
Requires:	mvn(org.eclipse.sisu:org.eclipse.sisu.inject) = 0.3.5
Requires:	mvn(org.eclipse.sisu:org.eclipse.sisu.plexus) = 0.3.5

%description
org.codehaus.modello 2.1.2 core and the java, xml, and xpp3 plugins.
ModelloCli generates the sources Maven 3.9.5 would otherwise build
with modello-maven-plugin. The Maven plugin itself is not packaged:
it compiles against Maven, which is the package this generator exists
to unblock.

%prep
%autosetup -n modello-%{name}-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"

CP="%{_javadir}/plexus-xml.jar"
CP="$CP:%{_javadir}/plexus-utils.jar"
CP="$CP:%{_javadir}/plexus-build-api.jar"
CP="$CP:%{_javadir}/org.eclipse.sisu.plexus-0.3.5.jar"
CP="$CP:%{_javadir}/org.eclipse.sisu.inject-0.3.5.jar"
CP="$CP:%{_javadir}/google-guice.jar"
CP="$CP:%{_javadir}/guava.jar"
CP="$CP:%{_javadir}/failureaccess.jar"
CP="$CP:%{_javadir}/atinject.jar"
CP="$CP:%{_javadir}/aopalliance.jar"
CP="$CP:%{_javadir}/plexus-classworlds-2.7.0.jar"
CP="$CP:%{_javadir}/plexus-containers/plexus-component-annotations.jar"
CP="$CP:%{_javadir}/slf4j-api.jar"
for jar in ${CP//:/ }; do
	test -s "$jar"
done

compile_mod() {
	src=$1
	out=$2
	expect=$3
	extra=$4
	mkdir -p "$out"
	find "$src" -name '*.java' ! -name 'module-info.java' > "$out.list"
	test "$(wc -l < "$out.list")" -eq "$expect"
	javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
		-cp "$CP:$extra" -d "$out" @"$out.list"
}

compile_mod modello-core/src/main/java out/core 44 ""
compile_mod modello-plugins/modello-plugin-java/src/main/java out/java 31 out/core
compile_mod modello-plugins/modello-plugin-xml/src/main/java out/xml 9 "out/core:out/java"
compile_mod modello-plugins/modello-plugin-xpp3/src/main/java out/xpp3 5 "out/core:out/java:out/xml"
javap -verbose -cp out/core org.codehaus.modello.Modello | grep -F -q 'major version: 52'

python - << 'PY'
import pathlib
import re
pairs = [
    ("out/core", "modello-core/src/main/java", 4),
    ("out/java", "modello-plugins/modello-plugin-java/src/main/java", 2),
    ("out/xml", "modello-plugins/modello-plugin-xml/src/main/java", 1),
    ("out/xpp3", "modello-plugins/modello-plugin-xpp3/src/main/java", 4),
]
for out, src, expect in pairs:
    names = []
    for path in pathlib.Path(src).rglob("*.java"):
        text = path.read_text(encoding="utf-8")
        if "@Component" not in text:
            continue
        match = re.search(r"^package ([^;]+);", text, re.M)
        if not match:
            raise SystemExit("no package in " + str(path))
        names.append(match.group(1) + "." + path.stem)
    names.sort()
    if len(names) != expect:
        raise SystemExit(out + " index " + str(len(names)))
    dest = pathlib.Path(out) / "META-INF" / "sisu"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "javax.inject.Named").write_text("\n".join(names) + "\n", encoding="utf-8")
PY
grep -F -q 'org.codehaus.modello.core.DefaultModelloCore' out/core/META-INF/sisu/javax.inject.Named
grep -F -q 'org.codehaus.modello.plugin.java.JavaModelloGenerator' out/java/META-INF/sisu/javax.inject.Named
grep -F -q 'org.codehaus.modello.plugins.xml.metadata.XmlMetadataPlugin' out/xml/META-INF/sisu/javax.inject.Named
grep -F -q 'org.codehaus.modello.plugin.xpp3.Xpp3ExtendedReaderGenerator' out/xpp3/META-INF/sisu/javax.inject.Named

mkdir -p out/xml/META-INF/modello
cp -f modello-plugins/modello-plugin-xml/src/main/resources/META-INF/modello/plugins.xml \
	out/xml/META-INF/modello/

jar_mod() {
	name=$1
	classes=$2
	jar cf "$name.jar" -C "$classes" .
	jar i "$name.jar"
	jar tf "$name.jar" | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
}
jar_mod modello-core out/core
jar_mod modello-plugin-java out/java
jar_mod modello-plugin-xml out/xml
jar_mod modello-plugin-xpp3 out/xpp3

cat > modello-core.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.codehaus.modello</groupId>
  <artifactId>modello-core</artifactId>
  <version>2.1.2</version>
  <name>Modello Core</name>
  <description>Modello 2.1.2 core. Plugins are separate jars.</description>
  <url>https://github.com/codehaus-plexus/modello</url>
  <licenses>
    <license>
      <name>MIT</name>
      <url>https://opensource.org/licenses/MIT</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-xml</artifactId>
      <version>4.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-utils</artifactId>
      <version>3.6.2</version>
    </dependency>
    <dependency>
      <groupId>org.sonatype.plexus</groupId>
      <artifactId>plexus-build-api</artifactId>
      <version>0.0.7</version>
    </dependency>
    <dependency>
      <groupId>org.eclipse.sisu</groupId>
      <artifactId>org.eclipse.sisu.plexus</artifactId>
      <version>0.3.5</version>
    </dependency>
    <dependency>
      <groupId>org.eclipse.sisu</groupId>
      <artifactId>org.eclipse.sisu.inject</artifactId>
      <version>0.3.5</version>
    </dependency>
    <dependency>
      <groupId>com.google.inject</groupId>
      <artifactId>guice</artifactId>
      <version>5.1.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>failureaccess</artifactId>
      <version>1.0.3</version>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
      <version>1.0.5</version>
    </dependency>
    <dependency>
      <groupId>aopalliance</groupId>
      <artifactId>aopalliance</artifactId>
      <version>1.0</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-classworlds</artifactId>
      <version>2.7.0</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-component-annotations</artifactId>
      <version>2.2.0</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>2.0.17</version>
    </dependency>
  </dependencies>
</project>
EOF

cat > modello-plugin-java.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.codehaus.modello</groupId>
  <artifactId>modello-plugin-java</artifactId>
  <version>2.1.2</version>
  <name>Modello Java Plugin</name>
  <description>Generates Java beans from a Modello model.</description>
  <url>https://github.com/codehaus-plexus/modello</url>
  <licenses>
    <license>
      <name>MIT</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.codehaus.modello</groupId>
      <artifactId>modello-core</artifactId>
      <version>2.1.2</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-utils</artifactId>
      <version>3.6.2</version>
    </dependency>
  </dependencies>
</project>
EOF

cat > modello-plugin-xml.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.codehaus.modello</groupId>
  <artifactId>modello-plugin-xml</artifactId>
  <version>2.1.2</version>
  <name>Modello XML Plugin</name>
  <description>Shared XML metadata for Modello generators.</description>
  <url>https://github.com/codehaus-plexus/modello</url>
  <licenses>
    <license>
      <name>MIT</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.codehaus.modello</groupId>
      <artifactId>modello-core</artifactId>
      <version>2.1.2</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.modello</groupId>
      <artifactId>modello-plugin-java</artifactId>
      <version>2.1.2</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-utils</artifactId>
      <version>3.6.2</version>
    </dependency>
  </dependencies>
</project>
EOF

cat > modello-plugin-xpp3.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.codehaus.modello</groupId>
  <artifactId>modello-plugin-xpp3</artifactId>
  <version>2.1.2</version>
  <name>Modello XPP3 Plugin</name>
  <description>Generates XPP3 readers and writers from a Modello model.</description>
  <url>https://github.com/codehaus-plexus/modello</url>
  <licenses>
    <license>
      <name>MIT</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.codehaus.modello</groupId>
      <artifactId>modello-plugin-java</artifactId>
      <version>2.1.2</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.modello</groupId>
      <artifactId>modello-plugin-xml</artifactId>
      <version>2.1.2</version>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-utils</artifactId>
      <version>3.6.2</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact modello-core.pom:modello-core.jar \
	--file-name modello-core \
	--filelist .mfiles
sysjar install --buildroot %{buildroot} \
	--artifact modello-plugin-java.pom:modello-plugin-java.jar \
	--file-name modello-plugin-java \
	--filelist .mfiles-java
sysjar install --buildroot %{buildroot} \
	--artifact modello-plugin-xml.pom:modello-plugin-xml.jar \
	--file-name modello-plugin-xml \
	--filelist .mfiles-xml
sysjar install --buildroot %{buildroot} \
	--artifact modello-plugin-xpp3.pom:modello-plugin-xpp3.jar \
	--file-name modello-plugin-xpp3 \
	--filelist .mfiles-xpp3
for extra in .mfiles-java .mfiles-xml .mfiles-xpp3; do
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
	done < "$extra"
done

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CORE=%{buildroot}%{_javadir}/modello-core.jar
PJAVA=%{buildroot}%{_javadir}/modello-plugin-java.jar
PXML=%{buildroot}%{_javadir}/modello-plugin-xml.jar
PXPP=%{buildroot}%{_javadir}/modello-plugin-xpp3.jar
for jar in "$CORE" "$PJAVA" "$PXML" "$PXPP"; do
	test -s "$jar"
done
RUNCP="$CORE:$PJAVA:$PXML:$PXPP"
RUNCP="$RUNCP:%{_javadir}/plexus-xml.jar"
RUNCP="$RUNCP:%{_javadir}/plexus-utils.jar"
RUNCP="$RUNCP:%{_javadir}/plexus-build-api.jar"
RUNCP="$RUNCP:%{_javadir}/org.eclipse.sisu.plexus-0.3.5.jar"
RUNCP="$RUNCP:%{_javadir}/org.eclipse.sisu.inject-0.3.5.jar"
RUNCP="$RUNCP:%{_javadir}/google-guice.jar"
RUNCP="$RUNCP:%{_javadir}/guava.jar"
RUNCP="$RUNCP:%{_javadir}/failureaccess.jar"
RUNCP="$RUNCP:%{_javadir}/atinject.jar"
RUNCP="$RUNCP:%{_javadir}/aopalliance.jar"
RUNCP="$RUNCP:%{_javadir}/plexus-classworlds-2.7.0.jar"
RUNCP="$RUNCP:%{_javadir}/plexus-containers/plexus-component-annotations.jar"
RUNCP="$RUNCP:%{_javadir}/slf4j-api.jar"

mkdir -p check
cat > check/check.mdo << 'EOF'
<?xml version="1.0"?>
<model xmlns="http://codehaus-plexus.github.io/MODELLO/1.4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://codehaus-plexus.github.io/MODELLO/1.4.0 http://codehaus-plexus.github.io/modello/xsd/modello-1.4.0.xsd">
  <id>check</id>
  <name>Check</name>
  <defaults>
    <default>
      <key>package</key>
      <value>org.example.check</value>
    </default>
  </defaults>
  <classes>
    <class rootElement="true">
      <name>Item</name>
      <version>1.0.0</version>
      <fields>
        <field>
          <name>title</name>
          <version>1.0.0</version>
          <type>String</type>
        </field>
      </fields>
    </class>
  </classes>
</model>
EOF
rm -rf check/gen
mkdir -p check/gen
java -cp "$RUNCP" org.codehaus.modello.ModelloCli check/check.mdo java check/gen 1.0.0 false 8 UTF-8
java -cp "$RUNCP" org.codehaus.modello.ModelloCli check/check.mdo xpp3-reader check/gen 1.0.0 false 8 UTF-8
java -cp "$RUNCP" org.codehaus.modello.ModelloCli check/check.mdo xpp3-writer check/gen 1.0.0 false 8 UTF-8
test -s check/gen/org/example/check/Item.java
test -s check/gen/org/example/check/io/xpp3/CheckXpp3Reader.java
test -s check/gen/org/example/check/io/xpp3/CheckXpp3Writer.java

cat > check/loc.mdo << 'EOF'
<?xml version="1.0"?>
<model xmlns="http://codehaus-plexus.github.io/MODELLO/1.4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://codehaus-plexus.github.io/MODELLO/1.4.0 http://codehaus-plexus.github.io/modello/xsd/modello-1.4.0.xsd">
  <id>loc</id>
  <name>Loc</name>
  <defaults>
    <default>
      <key>package</key>
      <value>org.example.loc</value>
    </default>
  </defaults>
  <classes>
    <class locationTracker="locations">
      <name>Location</name>
      <version>1.0.0</version>
      <fields/>
    </class>
    <class rootElement="true">
      <name>Root</name>
      <version>1.0.0</version>
      <fields>
        <field>
          <name>title</name>
          <version>1.0.0</version>
          <type>String</type>
        </field>
      </fields>
    </class>
  </classes>
</model>
EOF
java -cp "$RUNCP" org.codehaus.modello.ModelloCli check/loc.mdo xpp3-extended-reader check/gen 1.0.0 false 8 UTF-8
java -cp "$RUNCP" org.codehaus.modello.ModelloCli check/loc.mdo xpp3-extended-writer check/gen 1.0.0 false 8 UTF-8
test -s check/gen/org/example/loc/io/xpp3/LocXpp3ReaderEx.java

mkdir -p check/classes
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-cp "%{_javadir}/plexus-xml.jar:%{_javadir}/plexus-utils.jar" \
	-d check/classes $(find check/gen -name '*.java' -path '*/org/example/check/*')
cat > check/Round.java << 'EOF'
import java.io.StringReader;
import java.io.StringWriter;
import org.example.check.Item;
import org.example.check.io.xpp3.CheckXpp3Reader;
import org.example.check.io.xpp3.CheckXpp3Writer;
public class Round {
	public static void main(String[] args) throws Exception {
		Item item = new Item();
		item.setTitle("Hello");
		StringWriter sw = new StringWriter();
		new CheckXpp3Writer().write(sw, item);
		Item back = new CheckXpp3Reader().read(new StringReader(sw.toString()));
		System.out.println("modello_ok " + back.getTitle());
	}
}
EOF
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-cp "check/classes:%{_javadir}/plexus-xml.jar:%{_javadir}/plexus-utils.jar" \
	-d check/classes check/Round.java
java -cp "check/classes:%{_javadir}/plexus-xml.jar:%{_javadir}/plexus-utils.jar" Round > check/out.txt
cat check/out.txt
grep -F -q 'modello_ok Hello' check/out.txt

%files -f .mfiles
%license LICENSE.txt
%doc README.md
