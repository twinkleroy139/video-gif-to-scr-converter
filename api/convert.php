<?php
ini_set('display_errors', '0');
error_reporting(0);

require_once __DIR__ . '/../config.php';

header('Content-Type: application/json');

try {
    if (empty($_FILES) && empty($_POST) && isset($_SERVER['CONTENT_LENGTH']) && $_SERVER['CONTENT_LENGTH'] > 0) {
        throw new Exception('File upload exceeds server post_max_size limit.');
    }

    if (!isset($_FILES['video_file']) || $_FILES['video_file']['error'] !== UPLOAD_ERR_OK) {
        $error_code = isset($_FILES['video_file']['error']) ? $_FILES['video_file']['error'] : UPLOAD_ERR_NO_FILE;
        switch ($error_code) {
            case UPLOAD_ERR_INI_SIZE:
            case UPLOAD_ERR_FORM_SIZE:
                throw new Exception('File exceeds maximum allowed upload size.');
            case UPLOAD_ERR_PARTIAL:
                throw new Exception('File was only partially uploaded.');
            case UPLOAD_ERR_NO_FILE:
                throw new Exception('No file was uploaded.');
            default:
                throw new Exception('Upload error occurred (Code: ' . $error_code . ').');
        }
    }
    
    $file = $_FILES['video_file'];
    
    if ($file['size'] > MAX_FILE_SIZE) {
        throw new Exception('File too large. Maximum size: ' . (MAX_FILE_SIZE / 1024 / 1024) . 'MB');
    }
    
    $allowed = ['gif', 'mp4', 'webm', 'avi', 'mov'];
    $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    if (!in_array($ext, $allowed)) {
        throw new Exception('Unsupported file format. Allowed: ' . implode(', ', $allowed));
    }
    
    $input_name = uniqid() . '.' . $ext;
    $input_path = rtrim(UPLOAD_DIR, '/\\') . DIRECTORY_SEPARATOR . $input_name;
    
    if (!move_uploaded_file($file['tmp_name'], $input_path)) {
        throw new Exception('Failed to save uploaded file.');
    }
    
    $fps = isset($_POST['fps']) ? intval($_POST['fps']) : 15;
    $max_frames = isset($_POST['max_frames']) ? intval($_POST['max_frames']) : 150;
    $output_name = 'screensaver_' . uniqid();
    
    $is_windows = (PHP_OS_FAMILY === 'Windows');
    $python = $is_windows ? 'python' : 'python3';
    $script = PYTHON_SCRIPT;
    $output_target = rtrim(OUTPUT_DIR, '/\\') . DIRECTORY_SEPARATOR . $output_name;
    
    if ($is_windows) {
        $cmd = sprintf(
            'set PYTHONIOENCODING=utf-8 && %s "%s" "%s" -o "%s" -f %d -m %d 2>&1',
            $python, $script, $input_path, $output_target, $fps, $max_frames
        );
    } else {
        $cmd = sprintf(
            'PYTHONIOENCODING=utf-8 %s "%s" "%s" -o "%s" -f %d -m %d 2>&1',
            $python, $script, $input_path, $output_target, $fps, $max_frames
        );
    }
    
    exec($cmd, $output, $return_code);
    
    if (file_exists($input_path)) {
        unlink($input_path);
    }
    
    if ($return_code !== 0) {
        $error_msg = implode("\n", $output);
        throw new Exception('Conversion execution failed: ' . $error_msg);
    }
    
    $scr_file = $output_target . '.scr';
    if (!file_exists($scr_file)) {
        $files = glob($output_target . '.*');
        if (empty($files)) {
            throw new Exception('Screensaver generation failed. Logs: ' . implode("\n", $output));
        }
        $scr_file = $files[0];
    }
    
    $file_name = basename($scr_file);
    
    echo json_encode([
        'success' => true,
        'message' => 'Conversion completed successfully',
        'file' => $file_name,
        'download_url' => '/api/download.php?file=' . urlencode($file_name),
        'size' => filesize($scr_file)
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}