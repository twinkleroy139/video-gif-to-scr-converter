<?php
// Configuration
define('BASE_PATH', __DIR__);
define('UPLOAD_DIR', BASE_PATH . '/public/uploads/');
define('OUTPUT_DIR', BASE_PATH . '/public/output/');
define('MAX_FILE_SIZE', 50 * 1024 * 1024); // 50MB
define('PYTHON_SCRIPT', BASE_PATH . '/main.py');

// Create directories if they don't exist
if (!file_exists(UPLOAD_DIR)) mkdir(UPLOAD_DIR, 0777, true);
if (!file_exists(OUTPUT_DIR)) mkdir(OUTPUT_DIR, 0777, true);

// Clean old files (older than 1 hour)
function clean_old_files($dir, $age = 3600) {
    if (!file_exists($dir)) return;
    $files = glob($dir . '*');
    foreach ($files as $file) {
        if (is_file($file) && (time() - filemtime($file) > $age)) {
            unlink($file);
        }
    }
}
clean_old_files(UPLOAD_DIR);
clean_old_files(OUTPUT_DIR);
?>