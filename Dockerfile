FROM php:8.2-apache

# Install Python, modern OpenGL libraries, and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

COPY . /var/www/html/

# Install Python packages (using --break-system-packages for container environment)
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt pyinstaller

# Configure Apache document root to point to /public
ENV APACHE_DOCUMENT_ROOT /var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/000-default.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Ensure upload, output, and data folders exist with write permissions
RUN mkdir -p /var/www/html/public/uploads /var/www/html/public/output /var/www/html/data \
    && chown -R www-data:www-data /var/www/html/public/uploads /var/www/html/public/output /var/www/html/data \
    && chmod -R 775 /var/www/html/public/uploads /var/www/html/public/output /var/www/html/data

EXPOSE 80