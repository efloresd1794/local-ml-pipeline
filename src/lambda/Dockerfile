# Use AWS Lambda Python 3.9 base image
FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda function code
COPY inference.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "inference.handler" ]
