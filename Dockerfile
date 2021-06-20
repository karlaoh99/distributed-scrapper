FROM docker.uclv.cu/python:3.8-slim

RUN pip install Pyro4

RUN pip install requests

RUN pip install bs4

WORKDIR /scrapper
