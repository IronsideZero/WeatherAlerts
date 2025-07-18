FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

COPY ./requirements.txt ./
COPY ./config.json ./

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

#copy files/folders/etc from <host machine location> to <Image location>
COPY ./src ./src 

# Default command (can be overridden)
CMD ["python", "src/app.py"]