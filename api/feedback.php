<?php
header('Content-Type: application/json');

$feedback_file = __DIR__ . '/../data/feedback.json';
$data_dir = dirname($feedback_file);

if (!file_exists($data_dir)) {
    mkdir($data_dir, 0755, true);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $rating = isset($input['rating']) ? intval($input['rating']) : 0;
    $comment = isset($input['comment']) ? trim(strip_tags($input['comment'])) : '';
    
    if ($rating < 1 || $rating > 5) {
        echo json_encode(['success' => false, 'error' => 'Rating must be between 1 and 5']);
        exit;
    }
    
    $entry = [
        'id' => uniqid(),
        'rating' => $rating,
        'comment' => $comment,
        'timestamp' => date('Y-m-d H:i:s')
    ];
    
    $current_data = file_exists($feedback_file) ? json_decode(file_get_contents($feedback_file), true) : [];
    if (!is_array($current_data)) {
        $current_data = [];
    }
    
    $current_data[] = $entry;
    file_put_contents($feedback_file, json_encode($current_data, JSON_PRETTY_PRINT));
    
    echo json_encode(['success' => true, 'message' => 'Thank you for your feedback!']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $current_data = file_exists($feedback_file) ? json_decode(file_get_contents($feedback_file), true) : [];
    echo json_encode(['success' => true, 'feedbacks' => $current_data]);
    exit;
}