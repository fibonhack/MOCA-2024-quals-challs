#!/usr/bin/env bash

# echo "Remounting /proc for preventing users from seeing each other's processes..."
mount -o remount,hidepid=2 /proc

# echo "Disabling read of others users' data on /tmp..."
chmod 1732 /var/tmp /dev/shm

# echo "Protect your files"
chown root:root /pwnpeii

chmod 700 /pwnpeii

# echo "Changing ownership of problemuser..."
chown -R root:problemusers /home/problemuser

# echo "Setting permissions..."
chmod 750 /home/problemuser
chmod 550 -R /home/problemuser/*
chmod 440 -f /home/problemuser/flag.txt
chmod 440 -f /home/problemuser/flag

# echo "Writing the xinetd conf file..."
echo "
service ctf
{
	disable = no
	socket_type = stream
	protocol    = tcp
	wait        = no
	user        = root
	bind        = 0.0.0.0
	per_source  = 32
	cps         = 100 5
	server      = /pwnpeii/scripts/runner.sh
	port        = 6000
	rlimit_files = 8128
}" | tee /etc/xinetd.d/ctf

# echo "Adding new service to /etc/services"
echo "
ctf 6000/tcp
" >> /etc/services

# Run xinetd
/etc/init.d/xinetd start

# This runs forever
/pwnpeii/scripts/cleanup.sh
