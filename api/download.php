<?php
require_once __DIR__ . '/../config.php';

$file = isset($_GET['file']) ? basename($_GET['file']) : '';
if (empty($file)) {
    header('Location: /public/');
    exit;
}

$file_path = OUTPUT_DIR . $file;
if (!file_exists($file_path)) {
    header('HTTP/1.0 404 Not Found');
    echo 'File not found';
    exit;
}

// Serve the file
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $file . '"');
header('Content-Length: ' . filesize($file_path));
header('Cache-Control: no-cache');

readfile($file_path);

// Clean up after download
if (file_exists($file_path)) {
    unlink($file_path);
}
exit;
?>