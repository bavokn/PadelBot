FROM python:3.8-slim

RUN apt-get update && apt-get -y install python3-pip git nano
RUN python3 -m pip install -U pip

#add user
RUN useradd -ms /bin/bash user \
&& echo "user:user" | chpasswd \
&& usermod -aG audio user \
&& chpasswd && adduser user sudo

# Change terminal prompt
USER user
RUN echo 'export PS1="🐳 \[\033[01;32m\]\u@$CONTAINER_NAME\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> ~/.bashrc

COPY docker/requirements.txt ./
RUN python3 -m pip install --upgrade -r requirements.txt

#replace bugged file
# RUN rm /home/user/.local/lib/python3.8/site-packages/fbchat/_state.py
COPY docker/_state.py /home/user/.local/lib/python3.8/site-packages/fbchat/

USER user

WORKDIR /home/user/Documents/PadelBot

CMD ["python","-u", "padelBot.py"]