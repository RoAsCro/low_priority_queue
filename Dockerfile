FROM python
WORKDIR /app
COPY emails /app
RUN pip3 install -r ./requirements.txt
CMD ["gunicorn", "--bind","0.0.0.0:5003", "email_sender:run()"]