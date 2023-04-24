# Use an official Python runtime as a parent imag
FROM python:3.10
# Copy requirements.txt to the docker image and install packages
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# Expose port 8000
EXPOSE 8000
ENV PORT=8000
# Use gunicorn as the entrypoint
CMD ["uvicorn", "math_solver_app.app:app", "--host", "0.0.0.0", "--port", "8000"]
