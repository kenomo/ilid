FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

ENV TZ=Europe/Berlin
ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt -y install git curl libgl1-mesa-glx libglib2.0-0 msttcorefonts
# Hint: for using Arial in notebook you have to install msttcorefonts again accepting the terms of use

# Install miniconda
RUN cd /root && curl -O -J https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
ENV PATH="${PATH}:/root/miniconda3/bin"
RUN conda init bash

# Create working directory
RUN mkdir -p /root/ilid
WORKDIR /root/ilid

# Create conda environment
RUN conda create -y -n ilid python=3.8
RUN echo "conda activate ilid" >> $HOME/.bashrc
ENV CONDA_DEFAULT_ENV ilid
SHELL ["conda", "run", "-n", "ilid", "/bin/bash", "-c"]

# Install torch
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install bitsandbytes can be used for quantization
RUN pip3 install --user -i https://pypi.org/simple/ bitsandbytes

# Install other requirements
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

# Add pip bin packages to PATH
ENV PATH="${PATH}:/root/.local/bin"