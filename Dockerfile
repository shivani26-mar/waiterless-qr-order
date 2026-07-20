  FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8095
CMD ["streamlit", "run", "qr_hotel.py", "--server.port", "8095", "--server.address", "0.0.0.0"]

