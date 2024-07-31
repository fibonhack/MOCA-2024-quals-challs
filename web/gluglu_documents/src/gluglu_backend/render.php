<?php

// check content exists and is a string
if (isset($_POST["content"]) && is_string($_POST["content"])) {
    $content = $_POST["content"];

    // Create a temporary file to store the input JSON
    $inputFilePath = tempnam(sys_get_temp_dir(), 'input');
    file_put_contents($inputFilePath, json_encode(['html' => $content]));

    $DEBUG_PORT = 45098;
    // Execute the Node.js script
    $command = "DEBUG_PORT=" . $DEBUG_PORT . " node app/app.js < " . escapeshellarg($inputFilePath);
    $output = shell_exec($command);

    // Remove the temporary input file
    unlink($inputFilePath);

    if ($output === NULL) {
        // return 500
        http_response_code(500);
        exit();
    }

    // Decode the base64 output to binary
    $pdfContent = base64_decode($output);

    // return pdf
    header('Content-Type: application/pdf');
    echo $pdfContent;
    exit();
}

// return 404
http_response_code(404);
