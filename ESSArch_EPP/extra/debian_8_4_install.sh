echo "#

# deb cdrom:[Debian GNU/Linux 8.4.0 _Jessie_ - Official amd64 DVD Binary-1 20160402-14:46]/ jessie contrib main

#deb cdrom:[Debian GNU/Linux 8.4.0 _Jessie_ - Official amd64 DVD Binary-1 20160402-14:46]/ jessie contrib main

deb http://security.debian.org/ jessie/updates main contrib
deb-src http://security.debian.org/ jessie/updates main contrib

# jessie-updates, previously known as 'volatile'
# A network mirror was not selected during install.  The following entries
# are provided as examples, but you should amend them as appropriate
# for your mirror of choice.
#
# deb http://ftp.debian.org/debian/ jessie-updates main contrib
# deb-src http://ftp.debian.org/debian/ jessie-updates main contrib

# extra
deb http://httpredir.debian.org/debian jessie main
deb-src http://httpredir.debian.org/debian jessie main
deb http://httpredir.debian.org/debian jessie-updates main
deb-src http://httpredir.debian.org/debian jessie-updates main
#deb http://security.debian.org/ jessie/updates main
#deb-src http://security.debian.org/ jessie/updates main
deb http://www.rabbitmq.com/debian/ testing main
" > /etc/apt/sources.list

wget --no-check-certificate https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
apt-key add rabbitmq-signing-key-public.asc

apt-get update
apt-get dist-upgrade

apt-get install libssl-dev mysql-server libmysqlclient-dev libffi-dev unixodbc-dev sqlite3 libsqlite3-dev libreadline-dev libbz2-dev libgcrypt-dev libpcre3-dev rabbitmq-server xz-utils make

rabbitmq-plugins enable rabbitmq_management

groupadd arch
useradd -c "ESSArch System Account" -m -g arch arch
passwd arch

echo "### ESSArch start
#
export PATH=/ESSArch/pd/python/bin:$PATH:/usr/sbin
export LANG=en_US.UTF-8
export LD_LIBRARY_PATH=/ESSArch/pd/python/lib:/ESSArch/pd/libxslt/lib:/ESSArch/pd/libxml/lib:$LD_LIBRARY_PATH
export EPP=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP
export ETP=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_TP
export ETA=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_TA
export PYTHONPATH=$EPP:$EPP/workers:/ESSArch/config
export DJANGO_SETTINGS_MODULE=config.settings
alias bin='cd /ESSArch/bin'
alias log='cd /ESSArch/log'
#
### ESSArch end
" > /home/arch/.bash_profile

chown arch:arch /home/arch/.bash_profile

su - arch

wget --no-check-certificate https://github.com/ESSolutions/ESSArch_EPP/releases/download/2.7.3/ESSArch_EPP_installer-2.7.3.tar.gz
tar xvf ESSArch_EPP_installer-2.7.3.tar.gz
cd ESSArch_EPP_installer-2.7.3
./install

############################################################################
# Configure database:
# The MySQL commands listed below can be run within the mysql program, which may be invoked as follows.
# # mysql -u root -p
# 
# Create the database. For example, to create a database named "essarch", enter.
# mysql> CREATE DATABASE essarch DEFAULT CHARACTER SET utf8;
#
# Set username, password and permissions for the database. For example, to set the permissions for user "arkiv" with password "password" on database "essarch", enter:
# mysql> GRANT ALL ON essarch.* TO arkiv@localhost IDENTIFIED BY 'password';
#
############################################################################

# Create default tables in database

# Please run the following command as user: arch
# [arch@server ~]$ python $EPP/manage.py migrate
# [arch@server ~]$ python $EPP/extra/install_config.py


################################################
# sudo su -
# # export EPP=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP
#
# # cp $EPP/extra/celeryd.sh /etc/init.d/celeryd
# # chmod 744 /etc/init.d/celeryd
# # update-rc.d celeryd defaults
#
# # cp $EPP/extra/celerybeat.sh /etc/init.d/celerybeat
# # chmod 744 /etc/init.d/celerybeat
# # update-rc.d celerybeat defaults
#
# # cp $EPP/extra/httpd2.sh /etc/init.d/httpd
# # chmod 744 /etc/init.d/httpd
# # update-rc.d httpd defaults
#
# # cp $EPP/extra/ESSArch.sh /etc/init.d/essarch
# # chmod 744 /etc/init.d/essarch
# # update-rc.d essarch defaults
# 
# # cp /ESSArch/config/automysqlbackup/runmysqlbackup /etc/cron.daily/runmysqlbackup
# # chmod 744 /etc/cron.daily/runmysqlbackup
#
# # service celeryd start
# # service celerybeat start
# # service essarch start
# # service httpd start
