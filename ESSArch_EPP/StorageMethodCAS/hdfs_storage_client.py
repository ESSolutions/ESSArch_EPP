import requests

SERVER_PROTOCOL_PREFIX = 'http://'
SERVER_NAME = '81.189.135.189/dm-hdfs-storage'
SERVER_HDFS = SERVER_PROTOCOL_PREFIX + SERVER_NAME + '/hsink/fileresource'
FILE_RESOURCE = SERVER_HDFS + '/files/{0}'

def copy_to_hdfs(local_path):
    with open(local_path, 'r') as f:
        filename = local_path.rpartition('/')[2]
        r = requests.put(FILE_RESOURCE.format(filename), data=f)
        if (r.status_code == 201):
            return r.headers['location'].rpartition('/files/')[2]
        else:
            return ""

def copy_from_hdfs(hdfs_path, local_dir):
    r = requests.get(FILE_RESOURCE.format(hdfs_path), stream=True)
    filename = hdfs_path.rpartition('/')[2]
    with open(local_dir + '/' + filename, 'w') as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)

#hdfs_path = copy_to_hdfs('some_aip.tar')
#print(hdfs_path)
#if (hdfs_path != ""):
#    copy_from_hdfs(hdfs_path, 'local')

