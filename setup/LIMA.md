# Lima setup

1. Run `./lima.sh` to install lima via brew and configure it for docker

## M1 mac

1.  After the above step, run:
    `limactl shell default`
    `sudo systemctl start containerd`
    `sudo nerdctl run --privileged --rm tonistiigi/binfmt --install all`
    `exit`
    This enables running binaries from different formats on the M1 arm CPU
