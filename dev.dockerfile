FROM archlinux:base

# System Level Prereq's
RUN pacman -Syy
RUN pacman -S gcc git python python-pip --noconfirm

# Setup non-root user for development
RUN useradd --create-home --user-group --home-dir /home/dev --uid 1001 dev
USER dev
WORKDIR /home/dev

# Setup Octoprint dev environment
RUN git clone https://github.com/OctoPrint/OctoPrint ./octoprint
WORKDIR /home/dev/octoprint
RUN pip install -e .[develop,plugins]
RUN mkdir -p /home/dev/.octoprint/plugins
ENV PATH="${PATH}:/home/dev/.local/bin"
RUN pip install "https://github.com/kantlivelong/OctoPrint-PSUControl/archive/master.zip"

# Done
ENTRYPOINT "octoprint serve"
