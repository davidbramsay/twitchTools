Copy id_rsa and id_rsa.pub into ~/.ssh
Should now be able to get into remarkable with simple:

ssh root@10.11.99.1
(if not, password is in 'remarkablePassword.txt' and can be found in Settings>Help>Copyrights)
(ssh-keygen, scp ~/.ssh/id_rsa.pub root@10.11.99.1:~/.ssh/authorized_keys)
