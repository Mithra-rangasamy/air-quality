import os

hive_site = '/opt/hive/conf/hive-site.xml'
with open(hive_site, 'r') as f:
    content = f.read()

local_opt = """    <property>
        <name>hive.exec.mode.local.auto</name>
        <value>true</value>
    </property>
    <property>
        <name>hive.exec.mode.local.auto.inputbytes.max</name>
        <value>134217728</value>
    </property>
</configuration>"""

if 'hive.exec.mode.local.auto' not in content:
    content = content.replace('</configuration>', local_opt)
    with open(hive_site, 'w') as f:
        f.write(content)
    with open('/home/mithra/hive-site.xml', 'w') as f:
        f.write(content)
    print("Added local auto execution mode to hive-site.xml")
else:
    print("Already configured")
