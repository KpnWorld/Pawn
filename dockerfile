# Use a lean, official Python 3.11 image as the foundation
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies defined in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your local files (including bot.py) into the container
COPY . .

# Command to run the bot when the container starts
CMD ["python", "bot.py"]