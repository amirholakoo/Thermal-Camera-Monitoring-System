<?php
$conn = new mysqli("localhost", "root", "your_mysql_password", "engine_monitoring");

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$timestamp = $_POST['timestamp'];
$temperature = $_POST['temperature'];
$max_temperature = $_POST['max_temperature'];
$threshold_exceeded = $_POST['threshold_exceeded'] == 'true' ? 1 : 0;

$sql = "INSERT INTO temperature_data (timestamp, temperature, max_temperature, threshold_exceeded)
VALUES ('$timestamp', $temperature, $max_temperature, $threshold_exceeded)";

if ($conn->query($sql) === TRUE) {
    echo "Temperature data recorded successfully";
} else {
    echo "Error: " . $sql . "<br>" . $conn->error;
}

$conn->close();
?>
