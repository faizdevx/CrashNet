FROM python:3.10-slim
WORKDIR /app
COPY sensor_sim.py .
RUN pip install requests numpy
CMD ["python","sensor_sim.py"]
