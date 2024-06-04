FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

USER root

# Installs
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"
RUN apt-get update && apt-get install -y apt-transport-https && apt-get upgrade -y

# opencv from source
RUN apt-get install -y build-essential cmake git pkg-config libgtk-3-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libjpeg-dev libpng-dev libtiff-dev gfortran openexr libatlas-base-dev python3-dev python3-numpy libtbbmalloc2 libtbb-dev

# Build OpenCV
# https://www.howtoforge.com/how-to-install-open-source-computer-vision-library-opencv-on-ubuntu-22-04/

WORKDIR / 

RUN apt-get install -yq --reinstall ca-certificates

# Change working directory
WORKDIR /app

# Install Python packages in requirements.txt
COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# clone repos
RUN git clone -c http.sslverify=false https://github.com/opencv/opencv.git
RUN git clone -c http.sslverify=false https://github.com/opencv/opencv_contrib.git
RUN ls -la

WORKDIR /app/opencv
RUN mkdir build
WORKDIR /app/opencv/build

# setup the OpenCV build
RUN cmake -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local -DINSTALL_C_EXAMPLES=ON -DINSTALL_PYTHON_EXAMPLES=ON -DOPENCV_GENERATE_PKGCONFIG=ON -DOPENCV_EXTRA_MODULES_PATH=/app/opencv_contrib/modules -DBUILD_EXAMPLES=ON -DBUILD_opencv_legacy=OFF ..

# compile the OpenCV
RUN make -j8

# install OpenCV
RUN make install

USER 0

# Create licenses.txt
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -U pip-licenses
# RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -U pip-licenses

RUN mkdir /license

RUN echo "==============================================================================================" > /license/licenses.txt
RUN echo "======================================== PIP PACKAGES ========================================" >> /license/licenses.txt
RUN echo "==============================================================================================\n\n\n" >> /license/licenses.txt
RUN pip-licenses --format=plain-vertical --with-license-file --no-license-path --ignore-packages pip-licenses >> /license/licenses.txt
COPY ./application/FTL.TXT /license/FTL.TXT

RUN pip uninstall pip-licenses -y

# Copy required Code
COPY ./application/ /app/application/

USER 1001

# Expose port 5000
EXPOSE 5000

# Start FAST API Server!
CMD ["uvicorn", "application.main:app", "--reload", "--host=0.0.0.0", "--port=5000"] 
#, "--ssl-keyfile=/pvc/key.pem", "--ssl-certfile=/pvc/cert.pem"]
