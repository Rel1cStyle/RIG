# 
FROM python:3.10

# 
WORKDIR /app

# 
COPY requirements.txt /app/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY *.py /app/
COPY *.json /app/
COPY assets/ /app/assets/

# 
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:4111"]
