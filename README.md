# Lotte Harper
[![Django CI](https://github.com/daisycamber/lotteharper/actions/workflows/django.yml/badge.svg)](https://github.com/daisycamber/lotteharper/actions/workflows/django.yml)

## Automated, powerful computer vision and machine learning driven full stack software for professionals
Lotte Harper is a powerful, automated, machine learning driven full stack progressive web app built using Python, for expressive, social creators looking to build an online presence with modern software offering card and crypto payment processing with a number of processors, image, video, and audio upload and recording, ID scanning, enhanced biometric security features including facial recognition and biometric authentication as well as multi factor authentication and temporary one time codes, video chat (video meetings coming soon), games, voice donation, text to speech, transcription, image enhancement, programmable voice and SMS, a static frontend, marketing tools, remote control, recovery tools, full text search, an email server and integrated secure client, and a unix shell for authenticated administrators only. The software is also equipped with asynchronous tasks, a websocket server, stun server, and scheduled tasks. This is a full stack Python app with a purpose.

## About
This is a full stack web app focused on data visualization, machine learning, computer vision, facial recognition, biometrics, security, payment processing, marketing, ease of use, and more.

### Visit
Online at https://lotteh.com

### To deploy
You will need a web server, a VPS with Linux support and at least 8GB of RAM to run this software. Start by creating a web server and follow the instructions below to copy data to it. I recommend https://vultr.com or https://linode.com for a web server, although there are others, including https://ionos.com, https://kamatera.com and more, depending on your needs in particular, as most VPS and cloud providers support this project and cost under $100, or even under $50 to run each month for larger projects, or even less than $20 for an entry level server.
Generate API keys for Google recaptcha, maps, and all other desired APIs.
Make sure to update any neccesary settings in settings.py as well. Next, edit scripts/convert to denote new names for the domain, directory, project, and user. Cd to the directory and run scripts/convert with `./scripts/convert` before running `./scripts/setup` and allowing the software to install (may take 20-30 minutes depending on database, server constraints, etc). Alternativley, you can also run scripts/init from the project, being sure to paste in your SSH key in order to gain access to the machine - if you don't, you might get locked out depending on your hosting provider (usually they can accomodate this). You can also even download scripts/init seperatley or paste it into your hosting provider's script panel with the domain correctly configured to point to the server. Make sure to change the names in the last part of the file, your SSH key, and also update the git repo url if you would like to deploy and maintain private fork of the app using the script (adding .gitignore in the backup script to make sure this is not published by the open sourcing engine publishing this repo). Copy and paste the IP address, ipv6 address, domain key, and all other neccesary records into the DNS configuration including the OpenDKIM key (for the opendkim milter), make sure to print this key with `sudo cat /etc/opendkim/keys/lotteh.com/sendonly.txt | tr -d '\n' | sed 's/\s//g' | awk -F'[)(]' '{print $2}' | sed '0,/""/{s/""//}'` after initialize. Lastly, add a reverse DNS (rDNS) record to your server with the domain name you are using through your hosting provider.
I recommend also setting a user password and a root password, with `sudo passwd team` (where team is the name of the user denoted in the convert script.
If you want to change names of anything in the future, you can always run scripts/convert again, just make sure to switch the names you used last with the current names and update the old names with new names (in the variables in the beginning of the file).

To deploy, scripts/init looks like this:
```
#!/bin/bash
# This script will build the project from source according to custom names and the public repository by default (it is the counterpart of a private script that simply builds my deployment of the app, you can make it do a similar thing by adding your fork of the repo in the GIT url)
# Use your SSH key
SSH_KEY='<SSH key here>'
# Use the git repo from the project
GIT_REPO='https://github.com/daisycamber/lotteharper'
# Add your project name and username here
PROJECT_NAME="yourproject"
USER_NAME="team"
GIT_PROJ=`echo $GIT_REPO | rev | cut -d/ -f1 | rev`
sudo apt-add-repository universe
sudo apt install -y nano git expect
wget https://daisycamber.github.io/unix-config/sshd_config
sudo cp sshd_config /etc/ssh/sshd_config
#wget https://daisycamber.github.io/unix-config/lockout
#sudo cp lockout /etc/lockout
#sudo chmod a+x /etc/lockout
#echo "sh /etc/lockout" | sudo tee -a /etc/profile
#echo "session required pam_exec.so seteuid /etc/lockout" | sudo tee -a /etc/pam.d/sshd
sudo service ssh restart
sudo service sshd restart
echo "/root/.ssh/id_rsa" | sudo su root -c "ssh-keygen -t rsa -N ''"
echo "root ssh key:"
sudo su root -c "cat /root/.ssh/id_rsa.pub"
sudo adduser --disabled-password --gecos "" $USER_NAME
sudo passwd -d $USER_NAME
sudo usermod -aG sudo $USER_NAME
USER_RSA="/home/${USER_NAME}/.ssh/id_rsa"
echo $USER_RSA | su team -c "ssh-keygen -t rsa -N ''"
cat /home/$USER_NAME/.ssh/id_rsa.pub >> /home/$USER_NAME/.ssh/authorized_keys
echo $SSH_KEY >> /home/$USER_NAME/.ssh/authorized_keys
/usr/bin/expect <<EOD
cd /home/team
spawn git clone $GIT_REPO
set timeout -1
# If copying from a private repo, use a one time token, uncomment the below code
#expect "Username"
#send "your-git-email@example.com\n"
#expect "Password"
#send "<git otp here>\n"
#expect eof
#EOD
# Convert the software to use the name Makeup Girl, domain mupgirl.com, mupgirl directory and settings (must be the same as above two lines), and the name Daisy with (for example) with your email and a good mail name for your project user (i'm using team, above)
sudo su $USER_NAME -c "mv /home/$USER_NAME/$GIT_PROJ /home/$USER_NAME/$PROJECT_NAME"
sudo su $USER_NAME -c "mv /home/$USER_NAME/$PROJECT_NAME/lotteh /home/$USER_NAME/$PROJECT_NAME/$PROJECT_NAME"
sudo su $USER_NAME -c "sudo chown -R $USER_NAME:users /home/$USER_NAME/$PROJECT_NAME"
sudo su $USER_NAME -c "/home/$USER_NAME/$PROJECT_NAME/scripts/convert 'Makeup Girl' '<insert domain here, eg glamgirlx.com>' $PROJECT_NAME 'Daisy' your-letsencrypt-email@gmail.com" $USER_NAME
sudo su $USER_NAME -c "/home/$USER_NAME/$PROJECT_NAME/scripts/setup"
```

__Simply run the script in any Debian-like Bash shell, I recommend Ubuntu. Make sure to edit the names in the end and beginning of this file according to what you would like to call your deployment of this app.__

Please note that this code is being maintained and may not always function. If it does not install and become operational immediatley, please use the following commands in order:
(Inside the virtual environment and project directory)
```
# Use this command to finish setting up the requirements
pip3 install -r reqs.txt
# OR try, from the installed directory,
./scripts/resetvenv
# Check for install errors and fix
python manage.py check
# As long as everything works,
./scripts/pgsetup
# As well as
./scripts/sslsetup
# Start the services
sudo startservices
```

### Support
Looking for support for this software? Feel free to ask online or contact me using the links/email below.

Links:
https://glamgirlx.com/contact
https://glamgirlx.com/chat

Email:
team@lotteh.com
lotte.grace.harper@gmail.com

### Support me
I develop this software without compensation, so any support is appreciated! Please share this project with your friends, coworkers and community. Feel free to use the links below to support me, and share them with anyone who is interested. You may also hire me, buy/read my book (also on Amazon below), buy my photos, audio (I am a violinist :) and videos, subscribe to my blog, an ID scanning plan, or custom services on my website above.

#### Links
**Tip me in Crypto (fiat options available)**
https://lotteh.com/payments/crypto/Daisy/?crypto=USDC

**Read my book for free**
https://glamgirlx.com/practical-web-based-deep-learning-and

**Buy my book on Amazon** (Often on sale, and under development):
https://www.amazon.com/Practical-Based-Learning-Security-Example-ebook/dp/B0CJQZBDWK/ref=sr_1_1?crid=1L18HU0FLY875&dib=eyJ2IjoiMSJ9.Y18HxfGbnpOjl4_dNL5gdg.YQu4Z_qh8dKCi4DZfQV6b-sMRZz8c8s0RfQD_VGbGSc&dib_tag=se&keywords=Practical+web+based+deep+security+and+learning+by+example&qid=1730351216&sprefix=practical+web+based+deep+security+and+learning+by+example

**Buy a photo from me**
https://lotteh.com/payments/photo/Daisy/

**YouTube Channel**:
https://youtube.com/@daisymakeup

**Instagam** (code showcase and photos):
https://www.instagram.com/charlotte.grace.harper/profilecard/?igsh=aW5jazJ2bTQ0b2wz

**Twitter** (X):
https://twitter.com/teamfemmebabe

**My YouTube Playlist** (A playlist about this project)
https://www.youtube.com/playlist?list=PLM98ZFiLn-FGjYm-RNKteBj0YpNXNjZFR

### DNS config
__Sample DNS configuration:__
;; QUESTION SECTION:
;lotteh.com.			IN	TXT

;; ANSWER SECTION:
lotteh.com.		1799	IN	TXT	"v=BIMI1;l=https://lotteh.com/media/static/lotteh.svg"
lotteh.com.		1799	IN	TXT	"v=spf1 mx ip4:75.147.182.214 ip6:2601:602:8901:3914:725a:fff:fe49:3e02 ~all"

;; QUESTION SECTION:
;sendonly._domainkey.lotteh.com.	IN	TXT

;; ANSWER SECTION:
sendonly._domainkey.lotteh.com.	1796 IN	TXT	"v=DKIM1;h=sha256;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuD59wLd7aOqkO6u3lXt/eXVCoewxl4SbxXpGhhYzthxuNeDn9EHagSbLmMeYsF0gdY+fAEOtq26hdjvxGbe19ZEYOFP3tBYxXR8hYKE3F0fDQdwYR8aUvvXsImD0HmqvaDHrzjEjIn7EE6KLc++Gh6UC1KqVhyR7B3MfQSXo2y32g6HArxRCs+EdzF" "86yRQViLF+6uQNavoCkhFEI7TfqfwxV0gYFWjAs5NV/xoJiXeD457LsLiwM/uWfgVN7RIBNDxhuLBHAH4hvTtKXZdxol+ttMOtGbsbTaXH17ZrmfZd2bVswT3WR5eMRRtiX3M3r7+gQsuS0X2nxAdicfBpWwIDAQAB"

As well as A and AAAA record matching the SPF record above.

Note: This repo is automatically published by the software within every 12 hours and is usually in good shape to build at that time. If it's not working for you, consider pulling the repo again in a day or two to get a working copy of the app.

This website and it's use is governed by the [Code of Conduct](https://github.com/daisycamber/lotteharper/blob/main/CODE_OF_CONDUCT.md) and the privacy policy and terms of service at [lotteh.com/terms/](https://lotteh.com/terms/)

Questions? [Contact me at GlamGirlX.com](https://glamgirlx.com/contact)

### Thank you!
__Thank you for visiting, and for your interest in my project!__
- Charlotte Harper (Daisy)

__Watch my videos on YouTube >__
[![See my YouTube playlist recorded about this project, using the software](https://img.youtube.com/vi/1b79ArshiHI/0.jpg)](https://www.youtube.com/watch?v=4ME4TEzJa1k&list=PLM98ZFiLn-FGjYm-RNKteBj0YpNXNjZFR)

#### Scan or click this code to visit my shared links <3
[![Scan or click here to visit my shared links](https://i.imgur.com/WJ8gHin.png)](https://lotteh.com/@Daisy)

![A photo of me from my webiste Thanks for visiting!](https://i.imgur.com/dAQRaWt.jpeg)
__xoxo <3__
