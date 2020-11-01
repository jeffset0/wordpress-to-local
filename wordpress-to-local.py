import os
import paramiko
from scp import SCPClient
import logging
import gzip
import shutil
import fileinput
from config import (
    host,
    user,
    ssh_key,
    local_path,
    remote_path,
    db_name,
    db_username,
    db_password,
    filename,
    domain
)


logger = logging.getLogger('pyremote')


def createSSHClient(server, user, sshkey):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, username=user, key_filename=sshkey)
    return client


ssh = createSSHClient(host, user, ssh_key)
commands = ['tar --exclude=\'' + domain + '/wp-content/uploads/\' -czf \'' + domain + '/' + filename + '.tar.gz\' ' + domain, 'mysqldump -u ' + db_username + ' -p' + db_password + ' --add-drop-table ' + db_name + ' | gzip > ' + remote_path + filename + '.sql.gz']

def main():
    for command in commands:
        (stdin, stdout, stderr) = ssh.exec_command(command)
        for line in stdout.readlines():
            print(line)
    
    
    scp = SCPClient(ssh.get_transport(), socket_timeout=1024)
    

    # Download tar file
    scp.get(remote_path + filename + '.tar.gz', local_path)
    print('Downloaded: ' + filename + '.tar.gz')


    # Download sql dump file
    scp.get(remote_path + filename + '.sql.gz', local_path)
    print('Downloaded: ' + filename + '.sql.gz')


    # Close ssh connection
    ssh.close()
       

    # Extract tar file
    shutil.unpack_archive(local_path + filename + '.tar.gz', local_path)
    

    # Extract sql dump file
    with gzip.open(local_path + filename + '.sql.gz', 'rb') as f_in:
        with open(local_path + domain + '.sql', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


    # Replace with localhost in sql dump file
    with fileinput.FileInput(local_path + domain + '.sql', inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace('(1,\'siteurl\',\'https://' + domain + '\',\'yes\')', '(1,\'siteurl\',\'http://' + domain + '\',\'yes\')').replace('(2,\'home\',\'https://' + domain + '\',\'yes\')', '(2,\'home\',\'http://localhost\',\'yes\')'), end='')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
    main()
