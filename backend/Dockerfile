# Dockerfile for FastAPI backend (main.py)
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code into the container
# This assumes main.py is in the same directory as the Dockerfile
COPY ./main.py .
# If you had other Python modules your main.py imports, copy them too:
# COPY ./your_module_folder/ ./your_module_folder/

# Expose the port Uvicorn will run on (must match CMD and Render's port setting)
EXPOSE 8000

# Command to run the Uvicorn server when the container starts
# It will look for an 'app' instance in a file named 'main.py'
# Runs on 0.0.0.0 to be accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]