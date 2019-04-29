#!/bin/bash -e

get_os_name(){
    if [[ "$(cat /etc/*-release | grep NAME=\"Ubuntu\" | wc -l)" != "0" ]]; then
        OS_NAME='ubuntu'
    elif [[ "$(cat /etc/*-release | grep NAME=Fedora | wc -l)" != "0" ]]; then
        OS_NAME='fedora'
    elif [[ "$(cat /etc/*-release | grep NAME=\"SLES\" | wc -l)" != "0" ]]; then
        OS_NAME='sles'
    elif [[ "$(cat /etc/*-release | grep NAME=\"openSUSE | wc -l)" != "0" ]]; then
	    OS_NAME='opensuse'
    elif [[ "$(cat /etc/*-release | grep NAME=\"CentOS | wc -l)" != "0" ]]; then
        OS_NAME='centos'
    else
        echo 'This os is not supported!'
        exit 1
    fi
    echo "OS_NAME is $OS_NAME"
}

install_fedora_pre_req(){
    curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo
    yum update -y
    yum install -y curl git mariadb-devel gcc cairo pango python36 python3-devel bzip2

    curl https://bootstrap.pypa.io/get-pip.py -so get-pip.py
    ln -fs /usr/bin/python3.6 /usr/bin/python
    python get-pip.py
}

install_centos_pre_req(){
    yum install https://centos7.iuscommunity.org/ius-release.rpm -y
    yum update -y
    yum install -y curl git mariadb-devel gcc cairo pango python36u python36u-devel python36u-pip bzip2

    curl https://bootstrap.pypa.io/get-pip.py -so get-pip.py
    ln -fs /usr/bin/python3.6 /usr/bin/python
    python get-pip.py
}

install_sles_pre_req(){
    echo "sles/opensuse not yet supported"
    exit 1
}

install_ubuntu_pre_req(){
    apt-get update
    apt-get install -y curl python3.6 python3-pip python3.6-dev python3-cairocffi git pango1.0-tests postgresql-client libmariadbclient-dev

    ln -fs /usr/bin/python3.6 /usr/bin/python
}

install_pre_req(){
    if [[ ${OS_NAME} == 'centos' ]]; then
        install_centos_pre_req
    elif [[ ${OS_NAME} == 'fedora' ]]; then
        install_fedora_pre_req
    elif [[ ${OS_NAME} == 'ubuntu' ]]; then
        install_ubuntu_pre_req
    elif [[ ${OS_NAME} == 'sles' ]] || [[ ${OS_NAME} == 'opensuse' ]]; then
        install_sles_pre_req
    fi
}

get_os_name
install_pre_req

SCRIPT_LOCATION=$(dirname $0)
mkdir -p /ESSArch/log/
git clone https://github.com/ESSolutions/ESSArch_Core "$HOME/core"
python -m pip install -e $HOME/core/["tests,s3$DB_PACKAGES"]
cd ${SCRIPT_LOCATION}
coverage run ESSArch_PP/manage.py test -v2
