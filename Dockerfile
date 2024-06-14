# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Set the username as a build argument
ARG NORMALUSER=pluser

# Create a non-root user
RUN useradd -m $NORMALUSER

# Change ownership of the application directory to the new user
RUN chown -R $NORMALUSER:$NORMALUSER /app

# Switch to the new user
USER $NORMALUSER

# Add ~/.local/bin to the PATH for the new user
ENV PATH="/home/$NORMALUSER/.local/bin:${PATH}"

COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
# use tsinghua pypi mirror
RUN pip install --no-cache-dir -r requirements.txt

# pip install before copy . . to avoid rerunning pip install everything this
# directory changes
# Copy all of the application code into the container
COPY . .

# collect static files
#RUN python3 manage.py collectstatic --noinput

## Specify the command to run on container start
#CMD ["python3", "manage.py", "runserver"]
# Specify the command to run Gunicorn on container start
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "paperlistbackend.wsgi:application"]
