FROM python:3.10-slim

ENV CONTAINER_HOME=/var/www

# Set working directory
WORKDIR $CONTAINER_HOME

# Copy requirements and install dependencies
COPY requirements.txt $CONTAINER_HOME/requirements.txt
RUN pip install --no-cache-dir -r $CONTAINER_HOME/requirements.txt

# Copy application files
COPY app.py routes.py init.json $CONTAINER_HOME/
COPY models/ $CONTAINER_HOME/models/
COPY static/ $CONTAINER_HOME/static/
COPY templates/ $CONTAINER_HOME/templates/

# Run the Flask application using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]

