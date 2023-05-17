if you have existing id_rsa and id_rsa.pub in ~/.ssh, you can use:
ssh-copy-id root@10.11.99.1   
Otherwise need to generate with ssh-keygen

ssh root@10.11.99.1
(if not, password is in 'remarkablePassword.txt' and can be found in Settings>Help>Copyrights)
(ssh-keygen, scp ~/.ssh/id_rsa.pub root@10.11.99.1:~/.ssh/authorized_keys)


for google vision API, install google CLI using

curl https://sdk.cloud.google.com | bash
gcloud init
gcloud projects create dramsayocrtext #this name must be unique to your project, of all projects ever created in gcloud
gcloud auth login
gcloud config set project dramsayocrtext
gcloud auth application-default login
gcloud auth application-default set-quota-project dramsayocrtext

enable API in google cloud console
enable billing in google cloud console ($1.50/1000 images)

Second time, gcloud init will simply allow you to select the project on 'gcloud
init'; skip to 'gcloud auth application-default login'
