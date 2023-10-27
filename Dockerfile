FROM ubuntu:jammy
#python:3.10.13
#COPY . /app

# sdaps stuff
ENV LANG=en_US.UTF-8 \
    TZ=Europe/Oslo \
    DEBIAN_FRONTEND=noninteractive \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

RUN export DEBIAN_FRONTEND="noninteractive" && \
    apt-get update && \
    apt-get install -y locales && \
    locale-gen en_US.UTF-8 && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8 && \
    apt-get install -y software-properties-common && \
    echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    echo 'tzdata tzdata/Areas select Europe' | debconf-set-selections && \
    echo 'tzdata tzdata/Zones/Europe select Oslo' | debconf-set-selections && \
    apt install -y tzdata && \
    add-apt-repository ppa:benjamin-sipsolutions/sdaps-stable && \
    apt-get update && \
    apt-get install -y packagekit-gtk3-module libcanberra-gtk3-module && \
    apt install -y adwaita-icon-theme-full && \
    apt install -y python3-cairo python3-pil python3-reportlab python3-gi-cairo zbar-tools texlive texlive-latex-extra texlive-base libpgf6 texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-lang-english texlive-science gir1.2-poppler-0.18 python3-opencv && \
    apt-get install -y python3-pip

RUN apt-get install -y sdaps


ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN apt-get update && apt-get install -y zbar-tools
RUN pip install -r requirements.txt




EXPOSE 8501
ENTRYPOINT ["streamlit","run"]
CMD ["app.py"]
