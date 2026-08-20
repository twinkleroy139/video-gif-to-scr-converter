<?php
require_once __DIR__ . '/../config.php';

$raw_file = isset($_GET['file']) ? $_GET['file'] : '';

// Strip out any duplicated download.php?file= prefix if present
if (strpos($raw_file, 'download.php?file=') !== false) {
    $raw_file = substr($raw_file, strrpos($raw_file, '=') + 1);
}

$file = basename($raw_file);

if (empty($file)) {
    header('Location: /');
    exit;
}

$file_path = OUTPUT_DIR . $file;

if (!file_exists($file_path)) {
    header('HTTP/1.0 404 Not Found');
    echo 'File not found on server.';
    exit;
}

header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $file . '"');
header('Content-Length: ' . filesize($file_path));
header('Cache-Control: no-cache');

readfile($file_path);
exit;