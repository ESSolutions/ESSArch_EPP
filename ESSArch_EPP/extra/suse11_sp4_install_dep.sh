# zypper addrepo -c -t yast2 "iso:/?iso=/root/SLE-11-SP4-SDK-DVD-x86_64-GM-DVD1.iso" "SUSE-Linux-Enterprise-Software-Development-Kit-11-SP4"
# zypper addrepo http://download.opensuse.org/repositories/devel:languages:erlang/SLE_11_SP4/devel:languages:erlang.repo
# zypper addrepo http://download.opensuse.org/repositories/home:ghaskins:erlang/SLE_11_SP1/home:ghaskins:erlang.repo

zypper install kernel-default-devel \
sysstat \
make \
patch \
erlang \
gcc \
gcc-c++ \
openssl \
libopenssl-devel \
openldap2 \
openldap2-devel \
mt_st \
mtx \
sg3_utils \
mysql-client \
mysql \
libmysqlclient-devel \
libmysqlclient15 \
gnutls \
libreadline5 \
readline-devel \
unixODBC \
unixODBC-devel \
pcre \
pcre-devel \
liblzo2-2 \
lzo-devel \
xz \
libbz2-devel \
libffi-devel \
sqlite3 \
sqlite3-devel \
rabbitmq-server