FROM python:3.10
WORKDIR /app
ADD ./emails/requirements.txt /app/requirements.txt
RUN pip3 install -r ./requirements.txt
COPY emails /app
EXPOSE 5003
CMD ["gunicorn", "--bind","0.0.0.0:5003", "email_sender:run()"]