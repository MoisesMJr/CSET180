FROM python:3.9.7

# Set environment variables
# host.docker.internal instead of localhost
ENV FLASK_APP=main.py \
    FLASK_DEBUG=1 \
    FLASK_ENV=development \
    MYSQL_URI="mysql://newuser:Thaddeus911!@host.docker.internal:3306/ecommerce"

#MYSQL_URI="mysql://newuser:@host.docker.internal/test"
#MYSQL_URI="mysql://root:''@host.docker.internal/test"

#mysql://b0840d8d0eb823:5623c108@us-cdbr-east-05.cleardb.net/heroku_d8f6042e93d22cf
#root = b0840d8d0eb823
#pw = 5623c108
#localhost or 12.0.1.1 = us-cdbr-east-05.cleardb.net

# Lets make an app directory in the container to hold our files
RUN mkdir /app
WORKDIR /app

# Copy all files into our app working directory
COPY . /app
ADD . /app

# Install our requirements.txt
RUN pip install -r requirements.txt

# Copy our files again so we do not have to
# install requirements.txt again
COPY . .

# Run our app
ENTRYPOINT ["python", "./app.py"]
