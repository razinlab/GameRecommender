FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy your requirements file into the image
COPY requirements.txt .

# Install all dependencies directly into Lambda's expected directory
RUN pip install --no-cache-dir -r requirements.txt --platform manylinux2014_x86_64 \
    --target "${LAMBDA_TASK_ROOT}" --implementation cp --only-binary=:all: --upgrade

# Copy your actual app code
COPY . .
RUN mkdir -p /var/task/data

# Copy your application code
COPY *.py /var/task/
COPY *.csv /var/task/data/
COPY *.npy /var/task/data/

# Set the Lambda function entrypoint
CMD ["lambda_function.lambda_handler"]
