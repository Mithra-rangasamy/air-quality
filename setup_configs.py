import os, shutil

core_xml = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.proxyuser.mithra.hosts</name>
        <value>*</value>
    </property>
    <property>
        <name>hadoop.proxyuser.mithra.groups</name>
        <value>*</value>
    </property>
</configuration>
"""

hive_xml = """<?xml version="1.0"?>
<configuration>
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:derby:;databaseName=/home/mithra/hive_metastore_db;create=true</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>org.apache.derby.jdbc.EmbeddedDriver</value>
    </property>
    <property>
        <name>hive.server2.thrift.bind.host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>hive.server2.thrift.port</name>
        <value>10000</value>
    </property>
    <property>
        <name>hive.server2.enable.doAs</name>
        <value>false</value>
    </property>
    <property>
        <name>hive.server2.authentication</name>
        <value>NONE</value>
    </property>
    <property>
        <name>hive.metastore.schema.verification</name>
        <value>false</value>
    </property>
</configuration>
"""

# Backup core-site.xml if not already backed up
if not os.path.exists('/opt/hadoop/etc/hadoop/core-site.xml.bak_pre_ews'):
    shutil.copyfile('/opt/hadoop/etc/hadoop/core-site.xml', '/opt/hadoop/etc/hadoop/core-site.xml.bak_pre_ews')

with open('/opt/hadoop/etc/hadoop/core-site.xml', 'w') as f:
    f.write(core_xml)

with open('/opt/hive/conf/hive-site.xml', 'w') as f:
    f.write(hive_xml)

with open('/home/mithra/hive-site.xml', 'w') as f:
    f.write(hive_xml)

# Guava jar fix
if os.path.exists('/opt/hive/lib/guava-22.0.jar'):
    shutil.copyfile('/opt/hive/lib/guava-22.0.jar', '/opt/hive/lib/guava-22.0.jar.bak')
    os.remove('/opt/hive/lib/guava-22.0.jar')

if os.path.exists('/opt/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar'):
    shutil.copyfile('/opt/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar', '/opt/hive/lib/guava-27.0-jre.jar')

# SLF4J binding warning
if os.path.exists('/opt/hive/lib/log4j-slf4j-impl-2.18.0.jar'):
    shutil.move('/opt/hive/lib/log4j-slf4j-impl-2.18.0.jar', '/opt/hive/lib/log4j-slf4j-impl-2.18.0.jar.bak')

os.system('chown -R mithra:mithra /opt/hadoop/etc/hadoop/core-site.xml')
os.system('chown -R mithra:mithra /home/mithra/hive-site.xml')
os.system('chown -R root:root /opt/hive/conf/hive-site.xml')

print("Config setup completed successfully.")
