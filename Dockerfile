FROM php:8.2-apache

# Install Python, OpenGL libraries, and dependencies
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

# Copy custom PHP configuration for large uploads
COPY custom-php.ini /usr/local/etc/php/conf.d/custom-php.ini

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt pyinstaller

# Enable Apache rewrite module
RUN a2enmod rewrite

# Configure Apache Document Root to /var/www/html
ENV APACHE_DOCUMENT_ROOT /var/www/html
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/000-default.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Allow .htaccess overrides
RUN sed -i '/<Directory \/var\/www\/>/,/<\/Directory>/ s/AllowOverride None/AllowOverride All/' /etc/apache2/apache2.conf

# Setup writeable directories and permissions
RUN mkdir -p /var/www/html/public/uploads /var/www/html/public/output /var/www/html/data \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 775 /var/www/html/public/uploads /var/www/html/public/output /var/www/html/data

EXPOSE 80