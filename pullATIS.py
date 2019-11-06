from paramiko import SSHClient
from scp import SCPClient
import os


def getAtisFile():
    if not os.path.exists(r'DATA\ATIS'):
        os.mkdir(r'DATA\ATIS')
    try:
        with os.scandir(r'DATA\ATIS\send-uvd') as files:
            for file in files:
                os.remove(file)
    except FileNotFoundError:
        pass
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect('192.168.51.101', port=22, username='root')
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(r'/data/ametist/send-uvd/', r'DATA\ATIS\\', recursive=True)
    # ssh.connect('192.168.51.102', port=22, username='root')
    # with SCPClient(ssh.get_transport()) as scp:
    #     scp.get(r'/data/ametist/send-uvd/', r'DATA\ATIS\\', recursive=True)

    with os.scandir('DATA\ATIS\send-uvd') as files:
        file_dic = {}
        file_list = []
        for file in files:
            if 'eng' in file.name:
                file_info = file.stat().st_ctime
                file_dic[file_info] = file.name
                file_list.append(file_info)
        atis_newest = max(file_list)
        atis_file = r'DATA\ATIS\send-uvd\\' + (file_dic[atis_newest])
    return atis_file


if __name__ == '__main__':
    getAtisFile()
