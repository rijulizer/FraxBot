# Start your image with a node base image
FROM python:3.9.7-slim

# The /app directory should act as the main application directory
WORKDIR /app


# Copy the app package and package-lock.json file
# COPY package*.json ./

# Copy local directories to the current local directory of our docker image (/app)
COPY ./src ./src
COPY ./mongodb_user_certificate.pem ./mongodb_user_certificate.pem
COPY ./requirements.txt /app/requirements.txt

ENV PYTHONPATH=/app:/src

# Start the app using serve command
RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -Ur requirements.txt

CMD [ "python", "/app/src/common/scheduler_module.py" ]

#pass arguments
#docker entrypoint
#add py path in docker file
