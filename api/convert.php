<?php
require_once __DIR__ . '/../config.php';

header('Content-Type: application/json');

try {
    // Check if file was uploaded
    if (!isset($_FILES['video_file']) || $_FILES['video_file']['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('No file uploaded or upload error occurred');
    }
    
    $file = $_FILES['video_file'];
    
    // Validate file size
    if ($file['size'] > MAX_FILE_SIZE) {
        throw new Exception('File too large. Maximum size: ' . (MAX_FILE_SIZE / 1024 / 1024) . 'MB');
    }
    
    // Validate file type
    $allowed = ['gif', 'mp4', 'webm', 'avi', 'mov'];
    $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    if (!in_array($ext, $allowed)) {
        throw new Exception('Unsupported file format. Allowed: ' . implode(', ', $allowed));
    }
    
    // Generate unique filenames
    $input_name = uniqid() . '.' . $ext;
    $input_path = rtrim(UPLOAD_DIR, '/\\') . DIRECTORY_SEPARATOR . $input_name;
    
    // Move uploaded file
    if (!move_uploaded_file($file['tmp_name'], $input_path)) {
        throw new Exception('Failed to save uploaded file');
    }
    
    // Get parameters
    $fps = isset($_POST['fps']) ? intval($_POST['fps']) : 10;
    $max_frames = isset($_POST['max_frames']) ? intval($_POST['max_frames']) : 200;
    $output_name = 'screensaver_' . uniqid();
    
    $python = 'python';
    $script = PYTHON_SCRIPT;
    $output_target = rtrim(OUTPUT_DIR, '/\\') . DIRECTORY_SEPARATOR . $output_name;
    
    // Add PYTHONIOENCODING to handle Unicode properly
    $cmd = sprintf(
        'set PYTHONIOENCODING=utf-8 && %s "%s" "%s" -o "%s" -f %d -m %d 2>&1',
        $python,
        $script,
        $input_path,
        $output_target,
        $fps,
        $max_frames
    );
    
    // Execute conversion
    exec($cmd, $output, $return_code);
    
    // Clean up input file
    if (file_exists($input_path)) {
        unlink($input_path);
    }
    
    if ($return_code !== 0) {
        $error_msg = implode("\n", $output);
        throw new Exception('Conversion failed: ' . $error_msg);
    }
    
    // Check if .scr was created
    $scr_file = $output_target . '.scr';
    if (!file_exists($scr_file)) {
        $files = glob($output_target . '.*');
        if (empty($files)) {
            throw new Exception('Screensaver file was not created. Output: ' . implode("\n", $output));
        }
        $scr_file = $files[0];
    }
    
    // Return success with download link
    $file_name = basename($scr_file);
    $download_url = '/public/output/' . $file_name;
    
    echo json_encode([
        'success' => true,
        'message' => 'Conversion completed successfully',
        'file' => $file_name,
        'download_url' => $download_url,
        'size' => filesize($scr_file)
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>