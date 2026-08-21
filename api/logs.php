<?php
header('Content-Type: application/json');

$log_file = __DIR__ . '/../data/app.log';

if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    if (file_exists($log_file)) {
        file_put_contents($log_file, '');
    }
    echo json_encode(['success' => true, 'message' => 'Logs cleared.']);
    exit;
}

if (!file_exists($log_file)) {
    echo json_encode(['success' => true, 'logs' => 'No logs recorded yet.']);
    exit;
}

$lines = file($log_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$recent_lines = array_slice($lines, -100);

echo json_encode([
    'success' => true,
    'total_entries' => count($lines),
    'logs' => $recent_lines
]);
exit;