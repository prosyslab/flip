FROM ubuntu:20.04

MAINTAINER ngocpq <phungquangngoc@gmail.com>

#############################################################################
# Requirements
#############################################################################

RUN \
  apt-get update -y && \
  apt-get install software-properties-common -y && \
  apt-get update -y && \
  apt-get install -y openjdk-8-jdk \
                git \
                build-essential \
				subversion \
				perl \
				curl \
				unzip \
				cpanminus \
				make \
                maven \
                pip \
                vim \
                && \
  pip install parse \
              tqdm \
              parmap \
              && \
  rm -rf /var/lib/apt/lists/*

# Java version
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

# Timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


#############################################################################
# Setup Defects4J
#############################################################################

# ----------- Step 1. Clone defects4j from github --------------
WORKDIR /
RUN git clone https://github.com/rjust/defects4j.git defects4j
COPY flex /flip

# ----------- Step 2. Initialize Defects4J ---------------------
WORKDIR /defects4j
RUN git checkout 12dc3da1e049866de3d6b5aa15d4189a698746eb
RUN cpanm --installdeps .
RUN ./init.sh

# ----------- Step 3. Add Defects4J's executables to PATH: ------
ENV PATH="/defects4j/framework/bin:${PATH}"  
#--------------

WORKDIR /flip/test
COPY scripts/*.py .
COPY patch ./patch
RUN mvn compile
